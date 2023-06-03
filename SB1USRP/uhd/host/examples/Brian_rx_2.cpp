//
// Copyright 2010-2011,2014 Ettus Research LLC
// Copyright 2018 Ettus Research, a National Instruments Company
//
// SPDX-License-Identifier: GPL-3.0-or-later
//
//
//
// Modified by:
//      Yuning (Brian) Zhang, 5/13/2022
//

#include <uhd/exception.hpp>
// #include "wavetable_Brian.hpp"
#include <uhd/types/tune_request.hpp>
#include <uhd/usrp/multi_usrp.hpp>
#include <uhd/utils/safe_main.hpp>
#include <uhd/utils/thread.hpp>
#include <boost/algorithm/string.hpp>
#include <boost/format.hpp>
#include <boost/lexical_cast.hpp>
#include <boost/program_options.hpp>
#include <chrono>
#include <complex>
#include <csignal>
#include <fstream>
#include <iostream>
#include <thread>   // to solve error: this_thread and std::chrono is not declared

namespace po = boost::program_options;

/***********************************************************************
 * Signal handlers
 **********************************************************************/
static bool stop_signal_called = false;
void sig_int_handler(int)
{
    stop_signal_called = true;
}



/***********************************************************************
 * recv_to_file function
 **********************************************************************/
template <typename samp_type>
void recv_to_file(uhd::usrp::multi_usrp::sptr usrp,   // a USRP object/(virtual) device
    const std::string& cpu_format,
    const std::string& wire_format,
    const std::string& data_file,
    size_t samps_per_buff,
    size_t num_requested_samples,
    double time_requested       = 0.0,
    double start_streaming_time = 10.0,
    bool bw_summary             = false,
    bool stats                  = false,
    bool null                   = false,
    bool enable_size_map        = false,
    bool continue_on_bad_packet = false,
    std::vector<size_t> rx_channel_nums = 0)
{
    size_t num_total_samps = 0;   // number of samples have received so far

    //// ====== Create a receive streamer ======
        uhd::stream_args_t stream_args(cpu_format, wire_format);
        stream_args.channels = rx_channel_nums;
        uhd::rx_streamer::sptr rx_stream = usrp->get_rx_stream(stream_args);

        uhd::rx_metadata_t rx_md;
        std::vector<samp_type> buff(samps_per_buff);

        std::ofstream datafile_strm;
        std::ofstream rx_metadatafile_strm;
        
        size_t num_rx_samps = 0;

        char full_file_name[200];
        char full_metafile_name[200];
        strcpy(full_file_name, data_file.c_str());
        strcat(full_file_name, ".dat");
        if (not null)
            datafile_strm.open(full_file_name, std::ofstream::binary);
        bool overflow_message = true;


    //// ====== Configurations ======
        // Setup streaming
            uhd::stream_cmd_t stream_cmd((num_requested_samples == 0)
                        ? uhd::stream_cmd_t::STREAM_MODE_START_CONTINUOUS
                        : uhd::stream_cmd_t::STREAM_MODE_NUM_SAMPS_AND_DONE);
        
        // Number of samples to receive
            stream_cmd.num_samps  = size_t(num_requested_samples);

        // time to receive samples
            stream_cmd.stream_now = false;
            uhd::time_spec_t time_to_recv = uhd::time_spec_t(start_streaming_time);
            stream_cmd.time_spec  = time_to_recv;
            rx_stream->issue_stream_cmd(stream_cmd);

        // Define starting and stop time when request a duration
            const auto start_time = std::chrono::steady_clock::now();
            const auto stop_time =
                start_time + std::chrono::milliseconds(int64_t(1000 * time_requested));

        // Define sizemap
            typedef std::map<size_t, size_t> SizeMap;
            SizeMap mapSizes;

        // Track time and samps between updating the BW summary
            auto last_update = start_time;
            unsigned long long last_update_samps = 0; 


        // --- prints ---
            std::cout << std::endl;
            std::cout << std::endl;
            std::cout << "Rx: Wait for less than " << time_to_recv.get_real_secs() << " seconds to start streaming..."
                << std::endl;
        // --------------


    //// ====== Keep running until... ======
    // Until either time expired (if a duration was given), until
    // the requested number of samples were collected (if such a number was
    // given), or until Ctrl-C was pressed.
        while (not stop_signal_called
            and (num_requested_samples != num_total_samps or num_requested_samples == 0)
            and (time_requested == 0.0 or std::chrono::steady_clock::now() <= stop_time)) {

                const auto now = std::chrono::steady_clock::now();

                num_rx_samps =
                    rx_stream->recv(&buff.front(), buff.size(), rx_md, 30.0, enable_size_map);

                // Define error cases
                    // - 1 - 
                    if (rx_md.error_code == uhd::rx_metadata_t::ERROR_CODE_TIMEOUT) {
                        std::cout << boost::format("Timeout while streaming") << std::endl;
                        break;
                    }

                    // - 2 - 
                    if (rx_md.error_code == uhd::rx_metadata_t::ERROR_CODE_OVERFLOW) {
                        if (overflow_message) {
                            overflow_message = false;
                            std::cerr
                                << boost::format(
                                    "Got an overflow indication. Please consider the following:\n"
                                    "  Your write medium must sustain a rate of %fMB/s.\n"
                                    "  Dropped samples will not be written to the file.\n"
                                    "  Please modify this example for your purposes.\n"
                                    "  This message will not appear again.\n")
                                    % (usrp->get_rx_rate() * sizeof(samp_type) / 1e6);
                        }
                        continue;
                    }

                    // - 3 - 
                    if (rx_md.error_code != uhd::rx_metadata_t::ERROR_CODE_NONE) {
                        std::string error = str(boost::format("Receiver error: %s") % rx_md.strerror());
                        if (continue_on_bad_packet) {
                            std::cerr << error << std::endl;
                            continue;
                        } else
                            throw std::runtime_error(error);
                    }


                if (enable_size_map) {
                    SizeMap::iterator it = mapSizes.find(num_rx_samps);
                    if (it == mapSizes.end())
                        mapSizes[num_rx_samps] = 0;
                    mapSizes[num_rx_samps] += 1;
                }

                num_total_samps += num_rx_samps;

                if (datafile_strm.is_open()) {
                    datafile_strm.write((const char*)&buff.front(), num_rx_samps * sizeof(samp_type));
                }

                if (bw_summary) {
                    last_update_samps += num_rx_samps;
                    const auto time_since_last_update = now - last_update;
                    if (time_since_last_update > std::chrono::seconds(1)) {
                        const double time_since_last_update_s =
                            std::chrono::duration<double>(time_since_last_update).count();
                        const double rate = double(last_update_samps) / time_since_last_update_s;
                        std::cout << "\t" << (rate / 1e6) << " Msps" << std::endl;
                        last_update_samps = 0;
                        last_update       = now;
                    }
                }            
        }   // while ends
        const auto actual_stop_time = std::chrono::steady_clock::now();


    //// ====== Shut down receiver ======
        stream_cmd.stream_mode = uhd::stream_cmd_t::STREAM_MODE_STOP_CONTINUOUS;
        rx_stream->issue_stream_cmd(stream_cmd);


    //// ====== Close files ======
        if (datafile_strm.is_open()) {
            datafile_strm.close();
        }

        // print Rx finishes
        std::cout<<std::endl;
        std::cout<< "Rx done!" <<std::endl;


    //// ====== Status check ======
        if (stats) {
            std::cout << std::endl;
            const double actual_duration_seconds =
                std::chrono::duration<float>(actual_stop_time - start_time).count();

            std::cout << boost::format("Received %d samples in %f seconds") % num_total_samps
                            % actual_duration_seconds
                    << std::endl;
            const double rate = (double)num_total_samps / actual_duration_seconds;
            std::cout << (rate / 1e6) << " Msps" << std::endl;

            if (enable_size_map) {
                std::cout << std::endl;
                std::cout << "Packet size map (bytes: count)" << std::endl;
                for (SizeMap::iterator it = mapSizes.begin(); it != mapSizes.end(); it++)
                    std::cout << it->first << ":\t" << it->second << std::endl;
            }
        }


    //// ====== Process Metadata ======
        long long rx_starting_tick = rx_md.time_spec.to_ticks(200e6);
        double rx_starting_sec = rx_md.time_spec.get_real_secs();
        std::cout << "Metadata Here... " << std::endl;
        std::cout << "  Streaming starting tick = " << rx_starting_tick << std::endl;
        std::cout << "  Streaming starting sec = " << rx_starting_sec 
                    << std::endl
                    << std::endl;
        
        if (not null){
            strcpy(full_metafile_name, data_file.c_str());
            strcat(full_metafile_name, "_metadata.dat");
            rx_metadatafile_strm.open(full_metafile_name, std::ofstream::binary);
            rx_metadatafile_strm.write((char*)&rx_starting_tick, sizeof(long long));
            rx_metadatafile_strm.close();


            std::cout << "===============================" << std::endl;
            std::cout << boost::format("Data is saved in data_file: %s") % full_file_name
                    << std::endl
                    << std::endl;

            std::cout << boost::format("Metadata is saved in file: %s") % full_metafile_name
                    << std::endl;
            std::cout << "===============================" << std::endl;
        }
} // recv_to_file ends







///////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////



/***********************************************************************
 * Main function
 **********************************************************************/
int UHD_SAFE_MAIN(int argc, char* argv[])
{
    // variables to be set by po
    std::string rx_args, data_file, data_type, rx_ant, rx_subdev, ref, wirefmt, pps, rx_channels;
    // std::string wave_type;
    size_t total_num_samps, spb;
    double rx_rate, freq, rx_gain, rx_bw, total_time, setup_time, rx_lo_offset, rx_start;
    // double wave_freq;
    // float T0 = 1e-6;

    // setup the program options
    po::options_description desc("Allowed options");
    // clang-format off
    desc.add_options()
        ("help", "help message")

        ("rx-ant", po::value<std::string>(&rx_ant)->default_value("AB"), "antenna selection")
        ("rx-args", po::value<std::string>(&rx_args)->default_value("addr=10.38.14.2"), "multi uhd device address args")
        ("rx-bw", po::value<double>(&rx_bw), "analog frontend filter bandwidth in Hz")
        ("rx-channels", po::value<std::string>(&rx_channels)->default_value("0"), "which channels to use (specify \"0\", \"1\", \"0,1\", etc)")
        ("rx-continue", "don't abort on a bad packet")
        ("rx-duration", po::value<double>(&total_time)->default_value(0), "total number of seconds to receive")
        ("rx-file", po::value<std::string>(&data_file)->default_value("usrp_samples.dat"), "name of the file to write binary samples to")
        ("rx-gain", po::value<double>(&rx_gain)->default_value(6), "gain for the RF chain")
        ("rx-int-n", "tune USRP with integer-N tuning")
        ("rx-lo-offset", po::value<double>(&rx_lo_offset)->default_value(0.0),
            "Offset for frontend LO in Hz (optional)")
        ("rx-nsamps", po::value<size_t>(&total_num_samps)->default_value(0), "total number of samples to receive (requested)")     
        ("rx-null", "Determine if run the code and save data to file. Add 'null' when you don't want to save the data. ")
        ("rx-progress", "periodically display short-term bandwidth")
        ("rx-rate", po::value<double>(&rx_rate)->default_value(200e6), "rate of incoming samples")
        ("rx-sizemap", "track packet size and display breakdown on exit")
        ("rx-skip-lo", "skip checking LO lock status")
        ("rx-start", po::value<double>(&rx_start)->default_value(15.0), "start streaming time")
        ("rx-stats", "show average bandwidth on exit")
        ("rx-subdev", po::value<std::string>(&rx_subdev)->default_value("B:AB"), "subdevice specification")
        ("rx-type", po::value<std::string>(&data_type)->default_value("double"), "sample type: double, float, or short")
                
        ("freq", po::value<double>(&freq)->default_value(100e6), "IF center frequency in Hz")
        ("pps", po::value<std::string>(&pps)->default_value("external"), "PPS source (internal, external, mimo, gpsdo)")
        ("ref", po::value<std::string>(&ref)->default_value("external"), "reference source (internal, external, mimo)")
        ("setup", po::value<double>(&setup_time)->default_value(1.0), "seconds of setup time")
        ("spb", po::value<size_t>(&spb)->default_value(10000), "samples per buffer")
        ("wirefmt", po::value<std::string>(&wirefmt)->default_value("sc16"), "wire format (sc8, sc16 or s16)")
    ;


    //// ====== Clang-format on ======
        po::variables_map vm;
        po::store(po::parse_command_line(argc, argv, desc), vm);
        po::notify(vm);



    //// ====== Print the help message ======
        if (vm.count("help")) {
            std::cout << boost::format("UHD Rx receiving by WiDeS %s") % desc << std::endl;
            std::cout << std::endl
                    << "This application streams data from a single channel of a USRP "
                        "device to a file.\n"
                    << std::endl;
            return ~0;
        }



    //// ====== Set the Rx info parameters ======
        // vm.count("x") > 0 means there is an option named "x" is found. 
        bool bw_summary             = vm.count("progress") > 0; // initial value = 1
        bool stats                  = vm.count("stats") > 0;    // initial value = 1
        bool null                   = vm.count("null") > 0;     // initial value = 1
        bool enable_size_map        = vm.count("sizemap") > 0;  // initial value = 1
        bool continue_on_bad_packet = vm.count("continue") > 0; // initial value = 1

        if (enable_size_map)
            std::cout << "Packet size tracking enabled - will only recv one packet at a time!"
                    << std::endl;


    //// ====== Create Rx USRP Devices ======
        std::cout << std::endl;
        std::cout << boost::format("Creating the usrp device with: %s...") % rx_args
                << std::endl;
        uhd::usrp::multi_usrp::sptr rx_usrp = uhd::usrp::multi_usrp::make(rx_args);



    //// ====== Select Sub-device (always has default value) ======
        rx_usrp->set_rx_subdev_spec(rx_subdev);
    


    //// ====== Print Device Info ======
        // "get_pp_string" will return:
        //  1. USRP clock device;
        //  2. board amount, and their references;
        std::cout << std::endl;
        std::cout << boost::format("Using RX Device: %s") % rx_usrp->get_pp_string()
                << std::endl;



    //// ====== Detect which channels to use ======
        // if build error: split is not member of boost, then add library:
        // #include <boost/algorithm/string.hpp>
        std::vector<std::string> rx_channel_strings;
        std::vector<size_t> rx_channel_nums;
        boost::split(rx_channel_strings, rx_channels, boost::is_any_of("\"',"));
        for (size_t ch_idx = 0; ch_idx < rx_channel_strings.size(); ch_idx++) {
            size_t chan = std::stoi(rx_channel_strings[ch_idx]);
            if (chan >= rx_usrp->get_rx_num_channels())
                throw std::runtime_error("Invalid Rx channel(s) specified.");
            else
                rx_channel_nums.push_back(std::stoi(rx_channel_strings[ch_idx]));
        }
            


    //// ====== Set mboard reference clock source (always has default value) ======
        rx_usrp->set_clock_source(ref);

        std::cout << std::endl;
        std::cout<<boost::format("The reference clock for the Rx is: %s...") % ref
                    <<std::endl;



    //// ====== Reset timestamp and pps (always has default value) ======
        std::cout << boost::format("Setting device timestamp to 0 for the next unknown PPS edge...") << std::endl;

        rx_usrp->set_time_source(pps);

        rx_usrp->set_time_unknown_pps(uhd::time_spec_t(0.0));  // set the next coming pps as t = 0;
        std::this_thread::sleep_for(
            std::chrono::milliseconds(200)); // wait for pps sync pulse
        std::cout << "Current Rx time is: " << rx_usrp->get_time_now(0).get_real_secs() << std::endl;
        
        std::cout<<std::endl;
        std::cout<<"t=0 timestamp set."
            <<std::endl;
        


    //// ====== Set the sample rate (always has default value) ======
        // set the Rx sample rate
        std::cout << std::endl;
        std::cout << boost::format("Setting Rx Rate: %f Msps...") % (rx_rate / 1e6) << std::endl;
        rx_usrp->set_rx_rate(rx_rate);  // remove the channels parameters or not?
        std::cout << boost::format("Actual Rx Rate: %f Msps...")
                        % (rx_usrp->get_rx_rate() / 1e6)
                << std::endl;
              


    //// ====== Configure each channel ======
        for (size_t ch_idx = 0; ch_idx < rx_channel_nums.size(); ch_idx++) {

            size_t channel = rx_channel_nums[ch_idx];
                
            std::cout << std::endl;
            std::cout << std::endl;
            std::cout << boost::format("Timed command: Setting Rx Freq: %f MHz...") 
                    % (freq / 1e6) << std::endl;
            std::cout << boost::format("Timed command: Setting Rx LO Offset: %f MHz...") 
                    % (rx_lo_offset / 1e6) << std::endl;


            // start timed command with tune: 
            rx_usrp->clear_command_time();
            rx_usrp->set_command_time(uhd::time_spec_t(4.0));  //operate any command after "set_command_time" at t sec;
            
                // timed command content:
                    uhd::tune_request_t rx_tune_request(freq, rx_lo_offset);
                    if (vm.count("rx-int-n"))
                        rx_tune_request.args = uhd::device_addr_t("mode_n=integer");
                    rx_usrp->set_rx_freq(rx_tune_request, channel);
                    std::this_thread::sleep_for(std::chrono::milliseconds(110)); //sleep 110ms (~10ms after retune occurs) to allow LO to lock

            rx_usrp->clear_command_time();


            // print setting results
            std::cout<<std::endl;
            std::cout << boost::format("Actual Rx Freq: %f MHz...")
                            % (rx_usrp->get_rx_freq(channel) / 1e6)
                    << std::endl;


            // set the rf gain (always has default value)
            std::cout << std::endl;
            std::cout << boost::format("Setting Rx Gain: %f dB...") % rx_gain << std::endl;
            rx_usrp->set_rx_gain(rx_gain, channel);
            std::cout << boost::format("Actual Rx Gain: %f dB...")
                            % rx_usrp->get_rx_gain(channel)
                    << std::endl;


            // set the analog frontend filter bandwidth
            if (vm.count("rx-bw")) {
                std::cout<<std::endl;
                std::cout << boost::format("Setting Rx Bandwidth: %f MHz...") % (rx_bw / 1e6)
                        << std::endl;
                rx_usrp->set_rx_bandwidth(rx_bw, channel);
                std::cout << boost::format("Actual Rx Bandwidth: %f MHz...")
                                % rx_usrp->get_rx_bandwidth(channel / 1e6)
                        << std::endl;
            }

            // set the antenna (always has default value)
            rx_usrp->set_rx_antenna(rx_ant, channel);
        }



    //// ====== Wait for Setup ======
        std::this_thread::sleep_for(std::chrono::seconds(int64_t(1 * setup_time))); // allow for some setup time



    //// ====== Check Ref and LO Lock detect ======
        // LO locking check
        std::vector<std::string> rx_sensor_names;
        const size_t rx_sensor_chan = rx_channel_nums.empty() ? 0 : rx_channel_nums[0];   // in this case, the value is still 0
        rx_sensor_names = rx_usrp->get_rx_sensor_names(rx_sensor_chan);

        if (std::find(rx_sensor_names.begin(), rx_sensor_names.end(), "lo_locked")
            != rx_sensor_names.end()) {
            uhd::sensor_value_t lo_locked = rx_usrp->get_rx_sensor("lo_locked", rx_sensor_chan);
            std::cout << std::endl;
            std::cout << boost::format("Checking Rx: %s ...") % lo_locked.to_pp_string()
                    << std::endl;
            UHD_ASSERT_THROW(lo_locked.to_bool());
        }

        rx_sensor_names = rx_usrp->get_mboard_sensor_names(0);
        if ((ref == "external")
            and (std::find(rx_sensor_names.begin(), rx_sensor_names.end(), "ref_locked")
                    != rx_sensor_names.end())) {
            uhd::sensor_value_t ref_locked = rx_usrp->get_mboard_sensor("ref_locked", 0);
            std::cout << std::endl;
            std::cout << boost::format("Checking Rx: %s ...") % ref_locked.to_pp_string()
                    << std::endl;
            UHD_ASSERT_THROW(ref_locked.to_bool());
        }



    //// ====== Rx streaming prints ======
        if (total_num_samps == 0) {
            std::signal(SIGINT, &sig_int_handler);
            std::cout << "Press Ctrl + C to stop streaming..." << std::endl;
        }

    
    
    //// ====== Start Rx ======
        recv_to_file<std::complex<double>>(
            rx_usrp, "fc64", wirefmt, data_file, spb, total_num_samps, \
            total_time, rx_start, bw_summary, stats, null, enable_size_map, \
            continue_on_bad_packet, rx_channel_nums);

    // finished
    std::cout << std::endl << "Done!" << std::endl << std::endl;
    
    return EXIT_SUCCESS;
}
