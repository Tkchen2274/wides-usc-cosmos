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
    unsigned long long num_requested_samples,
    double time_requested       = 0.0,
    double start_streaming_time = 10.0,
    bool bw_summary             = false,
    bool stats                  = false,
    bool null                   = false,
    bool enable_size_map        = false,
    bool continue_on_bad_packet = false,
    std::vector<size_t> rx_channel_nums = 0)
{
    unsigned long long num_total_samps = 0;

    //// ====== Create a receive streamer ======
        uhd::stream_args_t stream_args(cpu_format, wire_format);
        std::vector<size_t> channel_nums;
        stream_args.channels = rx_channel_nums;
        uhd::rx_streamer::sptr rx_stream = usrp->get_rx_stream(stream_args);

        uhd::rx_metadata_t md;
        std::vector<samp_type> buff(samps_per_buff);
        std::ofstream datafile_strm;
        std::ofstream rx_metadatafile_strm;
        
        size_t num_rx_samps = 0;
        // size_t idx = 1;

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
            std::cout << "  Wait for less than " << time_to_recv.get_real_secs() << " seconds to start streaming..."
                << std::endl
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
                rx_stream->recv(&buff.front(), buff.size(), md, 30.0, enable_size_map);

            // Define error cases
                // - 1 - 
                if (md.error_code == uhd::rx_metadata_t::ERROR_CODE_TIMEOUT) {
                    std::cout << boost::format("Timeout while streaming") << std::endl;
                    break;
                }

                // - 2 - 
                if (md.error_code == uhd::rx_metadata_t::ERROR_CODE_OVERFLOW) {
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
                if (md.error_code != uhd::rx_metadata_t::ERROR_CODE_NONE) {
                    std::string error = str(boost::format("Receiver error: %s") % md.strerror());
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

    // Shut down receiver
    stream_cmd.stream_mode = uhd::stream_cmd_t::STREAM_MODE_STOP_CONTINUOUS;
    rx_stream->issue_stream_cmd(stream_cmd);

    if (datafile_strm.is_open()) {
        datafile_strm.close();
    }

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
        long long rx_starting_tick = md.time_spec.to_ticks(200e6);
        double rx_starting_sec = md.time_spec.get_real_secs();
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





/***********************************************************************
 * check LO function
 **********************************************************************/
typedef std::function<uhd::sensor_value_t(const std::string&)> get_sensor_fn_t;

bool check_locked_sensor(std::vector<std::string> sensor_names,
    const char* sensor_name,
    get_sensor_fn_t get_sensor_fn,
    double setup_time)
{
    if (std::find(sensor_names.begin(), sensor_names.end(), sensor_name)
        == sensor_names.end())
        return false;

    auto setup_timeout = std::chrono::steady_clock::now()
                         + std::chrono::milliseconds(int64_t(setup_time * 1000));
    bool lock_detected = false;

    std::cout << boost::format("Waiting for \"%s\": ") % sensor_name;
    std::cout.flush();

    while (true) {
        if (lock_detected and (std::chrono::steady_clock::now() > setup_timeout)) {
            std::cout << " locked." << std::endl;
            break;
        }
        if (get_sensor_fn(sensor_name).to_bool()) {
            std::cout << "+";
            std::cout.flush();
            lock_detected = true;
        } else {
            if (std::chrono::steady_clock::now() > setup_timeout) {
                std::cout << std::endl;
                throw std::runtime_error(
                    str(boost::format(
                            "timed out waiting for consecutive locks on sensor \"%s\"")
                        % sensor_name));
            }
            std::cout << "_";
            std::cout.flush();
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
    std::cout << std::endl;
    return true;
}


///////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////



/***********************************************************************
 * Main function
 **********************************************************************/
int UHD_SAFE_MAIN(int argc, char* argv[])
{
    // variables to be set by po
    std::string args, file, type, ant, subdev, ref, wirefmt, pps, rx_channels;
    // std::string wave_type;
    size_t total_num_samps, spb;
    double rate, freq, gain, bw, total_time, setup_time, lo_offset, rx_start;
    // double wave_freq;
    // float T0 = 1e-6;

    // setup the program options
    po::options_description desc("Allowed options");
    // clang-format off
    desc.add_options()
        ("help", "help message")

        ("ant", po::value<std::string>(&ant)->default_value("AB"), "antenna selection")
        ("args", po::value<std::string>(&args)->default_value("addr=10.38.14.2"), "multi uhd device address args")
        ("bw", po::value<double>(&bw), "analog frontend filter bandwidth in Hz")
        ("channels", po::value<std::string>(&rx_channels)->default_value("0"), "which channels to use (specify \"0\", \"1\", \"0,1\", etc)")
        ("continue", "don't abort on a bad packet")
        ("duration", po::value<double>(&total_time)->default_value(0), "total number of seconds to receive")
        ("file", po::value<std::string>(&file)->default_value("usrp_samples.dat"), "name of the file to write binary samples to")
        ("freq", po::value<double>(&freq)->default_value(100e6), "IF center frequency in Hz")
        ("gain", po::value<double>(&gain)->default_value(6), "gain for the RF chain")
        ("int-n", "tune USRP with integer-N tuning")
        ("lo-offset", po::value<double>(&lo_offset)->default_value(0.0),
            "Offset for frontend LO in Hz (optional)")
        ("nsamps", po::value<size_t>(&total_num_samps)->default_value(0), "total number of samples to receive (requested)")     
        ("pps", po::value<std::string>(&pps)->default_value("external"), "PPS source (internal, external, mimo, gpsdo)")
        ("progress", "periodically display short-term bandwidth")
        ("rate", po::value<double>(&rate)->default_value(200e6), "rate of incoming samples")
        ("ref", po::value<std::string>(&ref)->default_value("external"), "reference source (internal, external, mimo)")
        ("null", "Determine if run the code and save data to file. Add 'null' when you don't want to save the data. ")
        ("setup", po::value<double>(&setup_time)->default_value(1.0), "seconds of setup time")
        ("sizemap", "track packet size and display breakdown on exit")
        ("skip-lo", "skip checking LO lock status")
        ("spb", po::value<size_t>(&spb)->default_value(10000), "samples per buffer")
        ("stats", "show average bandwidth on exit")
        ("start", po::value<double>(&rx_start)->default_value(15.0), "start streaming time")
        ("subdev", po::value<std::string>(&subdev)->default_value("B:AB"), "subdevice specification")
        ("type", po::value<std::string>(&type)->default_value("double"), "sample type: double, float, or short")
        // ("wave-type", po::value<std::string>(&wave_type)->default_value("OFDM"), "waveform type (SINE)")
        // ("wave-freq", po::value<double>(&wave_freq)->default_value(1e6), "waveform frequency in Hz")
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
        std::cout << boost::format("Creating the usrp device with: %s...") % args
                << std::endl;
        uhd::usrp::multi_usrp::sptr usrp = uhd::usrp::multi_usrp::make(args);



    //// ====== Select Sub-device (always has default value) ======
        usrp->set_rx_subdev_spec(subdev);
    


    //// ====== Print Device Info ======
        // "get_pp_string" will return:
        //  1. USRP clock device;
        //  2. board amount, and their references;
        std::cout << std::endl;
        std::cout << boost::format("Using RX Device: %s") % usrp->get_pp_string()
                << std::endl;



    //// ====== Detect which channels to use ======
        // if build error: split is not member of boost, then add library:
        // #include <boost/algorithm/string.hpp>
        std::vector<std::string> channel_strings;
        std::vector<size_t> channel_nums;
        boost::split(channel_strings, rx_channels, boost::is_any_of("\"',"));
        for (size_t ch_idx = 0; ch_idx < channel_strings.size(); ch_idx++) {
            size_t chan = std::stoi(channel_strings[ch_idx]);
            if (chan >= usrp->get_rx_num_channels())
                throw std::runtime_error("Invalid Rx channel(s) specified.");
            else
                channel_nums.push_back(std::stoi(channel_strings[ch_idx]));
        }
            


    //// ====== Set mboard reference clock source (always has default value) ======
        usrp->set_clock_source(ref);

        std::cout << std::endl;
        std::cout<<boost::format("The reference clock for the Rx is: %s...") % ref
                    <<std::endl;



    //// ====== Reset timestamp and pps (always has default value) ======
        std::cout << boost::format("Setting device timestamp to 0 for the next unknown PPS edge...") << std::endl;

        usrp->set_time_source(pps);
        usrp->set_time_unknown_pps(uhd::time_spec_t(0.0));  // set the next coming pps as t = 0;
        // usrp->set_time_next_pps(uhd::time_spec_t(0.0));
        std::this_thread::sleep_for(
            std::chrono::seconds(1)); // wait for pps sync pulse
        
        std::cout<<std::endl;
        std::cout<<"t=0 timestamp set."
            <<std::endl;
        


    //// ====== Set the sample rate (always has default value) ======
        // set the Rx sample rate
        std::cout << boost::format("Setting Rx Rate: %f Msps...") % (rate / 1e6) << std::endl;
        usrp->set_rx_rate(rate);  // remove the channels parameters or not?
        std::cout << boost::format("Actual Rx Rate: %f Msps...")
                        % (usrp->get_rx_rate() / 1e6)
                << std::endl;
              


    //// ====== Configure each channel ======
        for (size_t ch_idx = 0; ch_idx < channel_nums.size(); ch_idx++) {

            size_t channel = channel_nums[ch_idx];
                
            std::cout<<std::endl;
            std::cout << boost::format("Timed command: Setting Rx Freq: %f MHz...") 
                    % (freq / 1e6) << std::endl;
            std::cout << boost::format("Timed command: Setting Rx LO Offset: %f MHz...") 
                    % (lo_offset / 1e6) << std::endl;


            // start timed command with tune: 
            usrp->clear_command_time();
            usrp->set_command_time(uhd::time_spec_t(4.0));  //operate any command after "set_command_time" at t sec;
            
                // timed command content:
                    uhd::tune_request_t tune_request(freq, lo_offset);
                    if (vm.count("int-n"))
                        tune_request.args = uhd::device_addr_t("mode_n=integer");
                    usrp->set_rx_freq(tune_request, channel);
                    std::this_thread::sleep_for(std::chrono::milliseconds(110)); //sleep 110ms (~10ms after retune occurs) to allow LO to lock

            usrp->clear_command_time();


            // print setting results
            std::cout<<std::endl;
            std::cout << boost::format("Actual Rx Freq: %f MHz...")
                            % (usrp->get_rx_freq(channel) / 1e6)
                    << std::endl;


            // set the rf gain (always has default value)
            std::cout<<std::endl;
            std::cout << boost::format("Setting Rx Gain: %f dB...") % gain << std::endl;
            usrp->set_rx_gain(gain, channel);
            std::cout << boost::format("Actual Rx Gain: %f dB...")
                            % usrp->get_rx_gain(channel)
                    << std::endl;


            // set the analog frontend filter bandwidth
            if (vm.count("bw")) {
                std::cout<<std::endl;
                std::cout << boost::format("Setting Rx Bandwidth: %f MHz...") % (bw / 1e6)
                        << std::endl;
                usrp->set_rx_bandwidth(bw, channel);
                std::cout << boost::format("Actual Rx Bandwidth: %f MHz...")
                                % usrp->get_rx_bandwidth(channel / 1e6)
                        << std::endl;
            }

            // set the antenna (always has default value)
            usrp->set_rx_antenna(ant, channel);
        }



    //// ====== Wait for Setup ======
        std::this_thread::sleep_for(std::chrono::seconds(int64_t(1 * setup_time))); // allow for some setup time



    //// ====== Check Ref and LO Lock detect ======
        // LO locking check
        std::vector<std::string> rx_sensor_names;
        const size_t rx_sensor_chan = channel_nums.empty() ? 0 : channel_nums[0];   // in this case, the value is still 0
        rx_sensor_names = usrp->get_rx_sensor_names(rx_sensor_chan);

                    std::cout << std::endl;
                    std::cout << "Test: Rx sensor name: " << rx_sensor_names[0]
                            << std::endl;

        if (std::find(rx_sensor_names.begin(), rx_sensor_names.end(), "lo_locked")
            != rx_sensor_names.end()) {
            uhd::sensor_value_t lo_locked = usrp->get_rx_sensor("lo_locked", rx_sensor_chan);
            std::cout << boost::format("Checking Rx: %s ...") % lo_locked.to_pp_string()
                    << std::endl;
            UHD_ASSERT_THROW(lo_locked.to_bool());
        }

        rx_sensor_names = usrp->get_mboard_sensor_names(0);
        if ((ref == "external")
            and (std::find(rx_sensor_names.begin(), rx_sensor_names.end(), "ref_locked")
                    != rx_sensor_names.end())) {
            uhd::sensor_value_t ref_locked = usrp->get_mboard_sensor("ref_locked", 0);

                        std::cout << std::endl;
                        std::cout << "Test: Rx mboard sensor name: " << rx_sensor_names[0]
                                << std::endl;

            std::cout << boost::format("Checking Rx: %s ...") % ref_locked.to_pp_string()
                    << std::endl;
            UHD_ASSERT_THROW(ref_locked.to_bool());
        }


    ////// The following codes use the self-defined functino: "check_locked_sensor"
    // // check Ref and LO Lock detect
    // if (not vm.count("skip-lo")) {  // if need LO check
    //     check_locked_sensor(usrp->get_rx_sensor_names(channels),
    //         "lo_locked",
    //         [usrp, channels](const std::string& sensor_name) {
    //             return usrp->get_rx_sensor(sensor_name, channels);
    //         },
    //         setup_time);
    //     if (ref == "external") {
    //         check_locked_sensor(usrp->get_mboard_sensor_names(0),
    //             "ref_locked",
    //             [usrp](const std::string& sensor_name) {
    //                 return usrp->get_mboard_sensor(sensor_name);
    //             },
    //             setup_time);
    //     }
    // }

    if (total_num_samps == 0) {
        std::signal(SIGINT, &sig_int_handler);
        std::cout << "Press Ctrl + C to stop streaming..." << std::endl;
    }


/* 
    All parameters are passed by main function
        file                   --> file name to save data
        spb                    --> samples per buffer
        total_num_samps        --> requested sample amount to receive       
        total_time             --> requested time to receive
        bw_summary             --> bool from recv_to_file()
        stats                  --> bool from recv_to_file()
        null                   --> bool from recv_to_file()
        enable_size_map        --> bool from recv_to_file()
        continue_on_bad_packet --> bool from recv_to_file()

    
    Review:
        // vm.count("x") > 0 means there is an option named "x" is found. 
        bool bw_summary             = vm.count("progress") > 0;
        bool stats                  = vm.count("stats") > 0;
        bool null                   = vm.count("null") > 0;
        bool enable_size_map        = vm.count("sizemap") > 0;
        bool continue_on_bad_packet = vm.count("continue") > 0;

*/
#define recv_to_file_args(cpufmt) (usrp, cpufmt, wirefmt, file, spb, total_num_samps,\
            total_time, rx_start, bw_summary, stats, null, enable_size_map, \
            continue_on_bad_packet, channel_nums)
    // recv to file
    if (wirefmt == "s16") {
        if (type == "double")
            recv_to_file<double> recv_to_file_args("f64");
        else if (type == "float")
            recv_to_file<float> recv_to_file_args("f32");
        else if (type == "short")
            recv_to_file<short> recv_to_file_args("s16");
        else
            throw std::runtime_error("Unknown type " + type);
    } else {
        if (type == "double")
            recv_to_file<std::complex<double>> recv_to_file_args("fc64");
        else if (type == "float")
            recv_to_file<std::complex<float>> recv_to_file_args("fc32");
        else if (type == "short")
            recv_to_file<std::complex<short>> recv_to_file_args("sc16");
        else
            throw std::runtime_error("Unknown type " + type);
    }

    // finished
    std::cout << std::endl << "Done!" << std::endl << std::endl;
    
    return EXIT_SUCCESS;
}
