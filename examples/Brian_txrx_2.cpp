//
// Copyright 2010-2012,2014-2015 Ettus Research LLC
// Copyright 2018 Ettus Research, a National Instruments Company
//
// SPDX-License-Identifier: GPL-3.0-or-later
//


// #include "wavetable.hpp"
#include "wavetable_Brian.hpp"
#include <uhd/exception.hpp>
#include <uhd/types/tune_request.hpp>
#include <uhd/usrp/multi_usrp.hpp>
#include <uhd/utils/safe_main.hpp>
#include <uhd/utils/static.hpp>
#include <uhd/utils/thread.hpp>
#include <boost/algorithm/string.hpp>   // to solve error: split is not member of boost
#include <boost/filesystem.hpp>
#include <boost/format.hpp>
#include <boost/math/special_functions/round.hpp>
#include <boost/program_options.hpp>
#include <boost/thread/thread.hpp>
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
 * Utilities
 **********************************************************************/
//! Change to filename, e.g. from usrp_samples.dat to usrp_samples.00.dat,
//  but only if multiple names are to be generated.
std::string generate_out_filename(
    const std::string& base_fn, size_t n_names, size_t this_name)
{
    if (n_names == 1) {
        return base_fn;
    }

    boost::filesystem::path base_fn_fp(base_fn);
    base_fn_fp.replace_extension(boost::filesystem::path(
        str(boost::format("%02d%s") % this_name % base_fn_fp.extension().string())));
    return base_fn_fp.string();
}


/***********************************************************************
 * transmit_worker function
 * A function to be used as a boost::thread_group thread for transmitting
 **********************************************************************/
void transmit_worker(std::vector<std::complex<float>> buff,
    wave_table_class_Brian wave_table,
    uhd::tx_streamer::sptr tx_stream,
    uhd::tx_metadata_t tx_md,  // metadata
    size_t step,
    size_t index,
    int size_channels)
{
    std::vector<std::complex<float>*> buffs(size_channels, &buff.front());

    // send data until the signal handler gets called
    while (not stop_signal_called) {
        // fill the buffer with the waveform
        for (size_t n = 0; n < buff.size(); n++) {
            buff[n] = wave_table(index += step);
        }

        // send the entire contents of the buffer
        tx_stream->send(buffs, buff.size(), tx_md);

        tx_md.start_of_burst = false;
        tx_md.has_time_spec  = false;
    }

    // send a mini EOB packet
    tx_md.end_of_burst = true;
    tx_stream->send("", 0, tx_md);
}


/***********************************************************************
 * recv_to_file function
 **********************************************************************/
template <typename samp_type>
void recv_to_file(uhd::usrp::multi_usrp::sptr usrp,   // a USRP object/(virtual) device
    const std::string& cpu_format,
    const std::string& wire_format,
    // const std::string& channel,
    const std::string& full_file_name,
    const std::string& full_rx_metafile_name,
    size_t samps_per_buff,
    size_t  num_requested_samples,
    double time_requested       = 0.0,
    double start_streaming_time = 10.0,
    bool bw_summary             = false,
    bool stats                  = false,
    bool null                   = false,
    bool enable_size_map        = false,
    bool continue_on_bad_packet = false,
    std::vector<size_t> rx_channel_nums = 0,
    int round = 0)
    
{
    size_t  num_total_samps = 0;   // number of samples have received so far

    //// ====== Create a receive streamer ======
        uhd::stream_args_t stream_args(cpu_format, wire_format);
        stream_args.channels = rx_channel_nums;
        uhd::rx_streamer::sptr rx_stream = usrp->get_rx_stream(stream_args);

        uhd::rx_metadata_t rx_md;
        std::vector<samp_type> buff(samps_per_buff);

        std::ofstream datafile_strm;
        std::ofstream rx_metadatafile_strm;

        size_t num_rx_samps = 0;


        // char full_file_name[200];
        // char full_metafile_name[200];
        // strcpy(full_file_name, data_file.c_str());
        // strcat(full_file_name, ".dat");
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
            if (round == 0){
                std::cout << std::endl;
                std::cout << std::endl;
                std::cout << "Rx: Wait for less than " << time_to_recv.get_real_secs() << " seconds to start streaming..."
                    << std::endl;
            }
        // --------------


    //// ====== Keep running until... ======
    // Until either time expired (if a duration was given), until
    // the requested number of samples were collected (if such a number was
    // given), or until Ctrl-C was pressed.
        while (not stop_signal_called
            and (num_requested_samples != num_total_samps or num_requested_samples == 0)
            and (time_requested == 0.0 or std::chrono::steady_clock::now() <= stop_time))  {
                
                const auto now = std::chrono::steady_clock::now();

                num_rx_samps = 
                    rx_stream->recv(&buff.front(), buff.size(), rx_md, 30.0, enable_size_map);

                // Define error cases
                    // - 1 - 
                    if (rx_md.error_code == uhd::rx_metadata_t::ERROR_CODE_TIMEOUT) {
                        std::cout << std::endl;
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
        } //while ends
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


    //// ====== Save Rx Metadata ======
        long long rx_starting_tick = rx_md.time_spec.to_ticks(200e6);
        double rx_starting_sec = rx_md.time_spec.get_real_secs();
        if (round == 0){
            std::cout << std::endl;
            std::cout << "Rx Metadata Here... " << std::endl;
            std::cout << "  Streaming starting tick = " << rx_starting_tick << std::endl;
            std::cout << "  Streaming starting sec = " << rx_starting_sec 
                        << std::endl;
        }
        
        if (not null){
            // strcpy(full_metafile_name, data_file.c_str());
            // strcat(full_metafile_name, "_rx_metadata.dat");
            rx_metadatafile_strm.open(full_rx_metafile_name, std::ofstream::binary);
            rx_metadatafile_strm.write((char*)&rx_starting_tick, sizeof(long long));
            rx_metadatafile_strm.close();

            std::cout << std::endl;
            std::cout << "===============================" << std::endl;
            std::cout << boost::format("Data is saved in file: %s") % full_file_name
                    << std::endl;
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
    // transmit variables to be set by po
    std::string tx_args, wave_type, tx_ant, tx_subdev, tx_channels, signal_file;
    double tx_rate, tx_gain, tx_bw, tx_lo_offset, tx_start;

    // receive variables to be set by po
    std::string rx_args, data_file, data_type, rx_ant, rx_subdev, rx_channels;
    size_t total_num_samps;
    double rx_rate, rx_gain, rx_bw, rx_lo_offset, rx_start, total_time;
    int data_file_group, data_file_testid, data_file_N;
    
    //general variables
    float ampl;
    std::string pps, ref, wirefmt, both_args;
    double freq, setup_time;
    size_t spb;
    // char full_metafile_name[200];
    std::ofstream tx_metadatafile_strm;
    

    // setup the program options
    po::options_description desc("Allowed options");

    // clang-format off
    desc.add_options()
        ("help", "help message")

        // Tx parameters
        ("tx-ant", po::value<std::string>(&tx_ant)->default_value("AB"), "transmit antenna selection")
        ("tx-args", po::value<std::string>(&tx_args)->default_value("addr=10.38.14.1"), "uhd transmit device address args")
        ("tx-bw", po::value<double>(&tx_bw), "analog transmit filter bandwidth in Hz")
        ("tx-channels", po::value<std::string>(&tx_channels)->default_value("0"), "which TX channel(s) to use (specify \"0\", \"1\", \"0,1\", etc)")
        ("tx-gain", po::value<double>(&tx_gain)->default_value(0), "gain for the transmit RF chain")
        ("tx-int-n", "tune USRP TX with integer-N tuning")
        ("tx-lo-offset", po::value<double>(&tx_lo_offset)->default_value(0.0),
            "Offset for frontend LO in Hz (optional)")   
        ("tx-rate", po::value<double>(&tx_rate)->default_value(200e6), "rate of transmit outgoing samples")
        ("tx-signal", po::value<std::string>(&signal_file)->default_value("cosmos_-100MHz_to_100MHz_SR_200MS_norm_5"), "signal txt file name")
        ("tx-start", po::value<double>(&tx_start)->default_value(8.0), "Tx starts streaming time")
        ("tx-subdev", po::value<std::string>(&tx_subdev)->default_value("A:AB"), "transmit subdevice specification")
        ("wave-type", po::value<std::string>(&wave_type)->default_value("OFDM"), "waveform type (CONST, SQUARE, RAMP, SINE)")
        
        // Rx parameters
        ("rx-ant", po::value<std::string>(&rx_ant)->default_value("AB"), "receive antenna selection")
        ("rx-args", po::value<std::string>(&rx_args)->default_value("addr=10.38.14.2"), "uhd receive device address args")
        ("rx-bw", po::value<double>(&rx_bw), "analog receive filter bandwidth in Hz")
        ("rx-channels", po::value<std::string>(&rx_channels)->default_value("0"), "which RX channel(s) to use (specify \"0\", \"1\", \"0,1\", etc)")
        ("rx-continue", "don't abort on a bad packet")
        ("rx-duration", po::value<double>(&total_time)->default_value(0), "total number of seconds to receive")
        ("rx-file", po::value<std::string>(&data_file)->default_value("test_"), "name of the file to write binary samples to")
        ("rx-file-group", po::value<int>(&data_file_group)->default_value(1), "the group ID of the tests")
        ("rx-file-testid", po::value<int>(&data_file_testid)->default_value(1), "the starting test ID of the test")
        ("rx-file-N", po::value<int>(&data_file_N)->default_value(6), "the number of repeating data that captured from the same position")
        ("rx-gain", po::value<double>(&rx_gain)->default_value(6), "gain for the receive RF chain")
        ("rx-int-n", "tune USRP RX with integer-N tuning")
        ("rx-lo-offset", po::value<double>(&rx_lo_offset)->default_value(0.0),
            "Offset for frontend LO in Hz (optional)")   
        ("rx-nsamps", po::value<size_t>(&total_num_samps)->default_value(0), "total number of samples to receive")
        ("rx-null", "Determine if run the code and save data to file. Add 'rx-null' when you don't want to save the data. ")
        ("rx-progress", "periodically display short-term bandwidth")
        ("rx-rate", po::value<double>(&rx_rate)->default_value(200e6), "rate of receive incoming samples")
        ("rx-sizemap", "track packet size and display breakdown on exit")
        ("rx-start", po::value<double>(&rx_start)->default_value(10.0), "Tx starts streaming time")
        ("rx-stats", "show average bandwidth on exit")
        ("rx-subdev", po::value<std::string>(&rx_subdev)->default_value("B:AB"), "receive subdevice specification")  
        ("rx-type", po::value<std::string>(&data_type)->default_value("double"), "sample type in file: double, float, or short")
                
        //General
        ("both-args", po::value<std::string>(&both_args)->default_value("addr0=10.38.14.1,addr1=10.38.14.2"), "uhd transmit device address args")
        ("ampl", po::value<float>(&ampl)->default_value(float(1.0)), "amplitude of the waveform [0 to 0.7]")
        ("freq", po::value<double>(&freq)->default_value(100e6), "receive RF center frequency in Hz")
        ("pps", po::value<std::string>(&pps)->default_value("external"), "PPS source (internal, external, mimo, gpsdo)")
        ("ref", po::value<std::string>(&ref)->default_value("external"), "clock reference (internal, external, mimo, gpsdo)")
        ("setup", po::value<double>(&setup_time)->default_value(1.0), "seconds of setup time")
        ("spb", po::value<size_t>(&spb)->default_value(0), "samples per buffer, 0 for default")
        ("wirefmt", po::value<std::string>(&wirefmt)->default_value("sc16"), "specify the over-the-wire sample mode")
    ;


    //// ====== Clang-format on ======
        po::variables_map vm;
        po::store(po::parse_command_line(argc, argv, desc), vm);
        po::notify(vm);





for (int round = 0; round < data_file_N; round++){
    // initialization
    stop_signal_called = false;
    std::cout << std::endl;
    std::cout << std::endl;
    std::cout << std::endl;
    std::cout << "||||||||||||||||||||||||||||||||||||||||||||||||||||" << std::endl;

    //// ====== Print the help message ======
        if (vm.count("help")) {
            std::cout << boost::format("UHD single node controlled TxRx %s") % desc << std::endl;
            std::cout << std::endl
                  << "This application streams data from a single channel of a USRP "
                     "device to a file.\n"
                  << std::endl;
            return ~0;
        }



    /// ====== Set the Rx info parameters ======
        // vm.count("x") > 0 means there is an option named "x" is found. 
        bool bw_summary             = vm.count("rx-progress") > 0;  // initial value = 1
        bool stats                  = vm.count("rx-stats") > 0;     // initial value = 1
        bool null                   = vm.count("rx-null") > 0;      // initial value = 1
        bool enable_size_map        = vm.count("rx-sizemap") > 0;   // initial value = 1
        bool continue_on_bad_packet = vm.count("rx-continue") > 0;  // initial value = 1

        if (enable_size_map)
        std::cout << "Packet size tracking enabled - will only recv one packet at a time!"
                  << std::endl;



    //// ====== Create Tx and Rx USRP Devices ======
        // // Tx USRP
        // std::cout << std::endl;
        // std::cout << boost::format("Creating the Tx USRP device with: %s...") % tx_args
        //         << std::endl;
        // // uhd is defined at "<uhd/usrp/multi_usrp.hpp>" and implemented in "uhd/lib/.cpp" 
        // uhd::usrp::multi_usrp::sptr tx_usrp = uhd::usrp::multi_usrp::make(tx_args);

        // // Rx USRP
        // std::cout << std::endl;
        // std::cout << boost::format("Creating the Rx USRP device with: %s...") % rx_args
        //         << std::endl;
        // uhd::usrp::multi_usrp::sptr rx_usrp = uhd::usrp::multi_usrp::make(rx_args);

        // Both USRPs
        std::cout << std::endl;
        std::cout << boost::format("Creating both USRP devices with: %s...") % both_args
                << std::endl;
        // uhd is defined at "<uhd/usrp/multi_usrp.hpp>" and implemented in "uhd/lib/.cpp" 
        uhd::usrp::multi_usrp::sptr both_usrp = uhd::usrp::multi_usrp::make(both_args);



    //// ====== Select Sub-device (always has default value) ======
        both_args->set_tx_subdev_spec(tx_subdev, 0);
        both_args->set_rx_subdev_spec(rx_subdev, 1);


    
    //// ====== Print Device Info ======
        // "get_pp_string" will return:
        //  1. USRP clock device;
        //  2. board amount, and their references;
        if (round == 0){
            std::cout << std::endl;
            std::cout << boost::format("Using Devices: %s") % both_args->get_pp_string()
                    << std::endl;
        }



    //// ====== Detect which channels to use ======
        // if build error: split is not member of boost, then add library:
        // #include <boost/algorithm/string.hpp>

        // Tx channel
        std::vector<std::string> tx_channel_strings;
        std::vector<size_t> tx_channel_nums;
        boost::split(tx_channel_strings, tx_channels, boost::is_any_of("\"',"));
        for (size_t ch_idx = 0; ch_idx < tx_channel_strings.size(); ch_idx++) {
            size_t chan = std::stoi(tx_channel_strings[ch_idx]);
            if (chan >= tx_usrp->get_tx_num_channels())
                throw std::runtime_error("Invalid Tx channel(s) specified.");
            else
                tx_channel_nums.push_back(std::stoi(tx_channel_strings[ch_idx]));
        }

        // Rx channel
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
        tx_usrp->set_clock_source(ref);
        rx_usrp->set_clock_source(ref);

        if (round == 0){
            std::cout << std::endl;
            std::cout<<boost::format("The reference clock for both Tx/Rx is: %s...") % ref
                        <<std::endl;
        }


    //// ====== Reset timestamp and pps (always has default value) ======
        std::cout << std::endl;
        std::cout << boost::format("Setting device timestamp to 0 for the next unknown PPS edge...") << std::endl;

        tx_usrp->set_time_source(pps);
        rx_usrp->set_time_source(pps);
        
        // Tx initialization
        tx_usrp->set_time_unknown_pps(uhd::time_spec_t(0.0));  // set the next coming pps as t = 0;
        // std::this_thread::sleep_for(
        //     std::chrono::milliseconds(200)); // wait for pps sync pulse
        std::cout << "Current Tx time is: " << tx_usrp->get_time_now(0).get_real_secs() << std::endl;

        // Rx initialization
        rx_usrp->set_time_unknown_pps(uhd::time_spec_t(2.0));  // set the next coming pps as t = 0;
        std::this_thread::sleep_for(
            std::chrono::seconds(1)); // wait for pps sync pulse

        std::cout << "Verification: " << std::endl;
        double tx_time_now = tx_usrp->get_time_now(0).get_real_secs();
        double rx_time_now = rx_usrp->get_time_now(0).get_real_secs();
        std::cout << "  Current Tx time is: " << tx_time_now << std::endl;
        std::cout << "  Current Rx time is: " << rx_time_now << std::endl;
        double txrx_diff = rx_time_now - tx_time_now;
        std::cout << "Difference = " << txrx_diff << ", which should be very small (<1 at least)." 
            << std::endl;
        
        std::cout << std::endl;
        std::cout<<"t=0 timestamp set."
            <<std::endl;


    
    //// ====== Set the sample rate (always has default value) ======
        // set the Tx sample rate
        if (round == 0){
            std::cout << std::endl;
            std::cout << boost::format("Setting Tx Rate: %f Msps...") % (tx_rate / 1e6) << std::endl;
        }

        tx_usrp->set_tx_rate(tx_rate);  // remove the channels parameters or not?

        if (round == 0){
            std::cout << boost::format("Actual Tx Rate: %f Msps...")
                            % (tx_usrp->get_tx_rate() / 1e6)
                    << std::endl;
            }

        // set the Rx sample rate
        if (round == 0){
            std::cout << std::endl;
            std::cout << boost::format("Setting Rx Rate: %f Msps...") % (rx_rate / 1e6) << std::endl;
        }

        rx_usrp->set_rx_rate(rx_rate);  // remove the channels parameters or not?

        if (round == 0){
            std::cout << boost::format("Actual Rx Rate: %f Msps...")
                            % (rx_usrp->get_rx_rate() / 1e6)
                    << std::endl;
        }



    //// ====== Configure each channel ======
        // --- Tx channels ---
        for (size_t ch_idx = 0; ch_idx < tx_channel_nums.size(); ch_idx++) {

            size_t channel = tx_channel_nums[ch_idx];
            
            if (round == 0){
                std::cout << std::endl;
                std::cout << std::endl;
                std::cout << "----------------------------" <<std::endl;
                std::cout << boost::format("Timed command: Setting Tx Freq: %f MHz...") 
                        % (freq / 1e6) << std::endl;
                std::cout << boost::format("Timed command: Setting Tx LO Offset: %f MHz...") 
                        % (tx_lo_offset / 1e6) << std::endl;            
            }

            // start timed command with tune: 
            tx_usrp->clear_command_time();
            tx_usrp->set_command_time(uhd::time_spec_t(4.0));  //operate any command after "set_command_time" at t sec;           
            
                // timed command content:
                    uhd::tune_request_t tx_tune_request(freq, tx_lo_offset);
                    if (vm.count("tx-int-n"))
                        tx_tune_request.args = uhd::device_addr_t("mode_n=integer");
                    tx_usrp->set_tx_freq(tx_tune_request, channel);
                    std::this_thread::sleep_for(std::chrono::milliseconds(110)); //sleep 110ms (~10ms after retune occurs) to allow LO to lock

            tx_usrp->clear_command_time();


            // print setting results
            if (round == 0){
                std::cout << std::endl;
                std::cout << boost::format("Actual Tx Freq: %f MHz...")
                                % (tx_usrp->get_tx_freq(channel) / 1e6)
                        << std::endl;
                std::cout << "----------------------------" <<std::endl;
            }

            // set the rf gain (always has default value)
            if (round == 0){
                std::cout << std::endl;
                std::cout << boost::format("Setting Tx Gain: %f dB...") % tx_gain << std::endl;
            }

            tx_usrp->set_tx_gain(tx_gain, channel);

            if (round == 0){
                std::cout << boost::format("Actual Tx Gain: %f dB...")
                                % tx_usrp->get_tx_gain(channel)
                        << std::endl;
            }


            // set the analog frontend filter bandwidth
            if (vm.count("tx-bw")) {
                if (round == 0){
                    std::cout << std::endl;
                    std::cout << boost::format("Setting Tx Bandwidth: %f MHz...") % (tx_bw / 1e6)
                            << std::endl;
                }

                tx_usrp->set_tx_bandwidth(tx_bw, channel);

                if (round == 0){
                    std::cout << boost::format("Actual Tx Bandwidth: %f MHz...")
                                    % tx_usrp->get_tx_bandwidth(channel / 1e6)
                            << std::endl;
                }
            }

            // set the antenna (always has default value)
            tx_usrp->set_tx_antenna(tx_ant, channel);
        }


        // --- Rx channels ---
        for (size_t ch_idx = 0; ch_idx < rx_channel_nums.size(); ch_idx++) {

            size_t channel = rx_channel_nums[ch_idx];
                
            if (round == 0){
                std::cout << std::endl;
                std::cout << std::endl;
                std::cout << "----------------------------" <<std::endl;
                std::cout << boost::format("Timed command: Setting Rx Freq: %f MHz...") 
                        % (freq / 1e6) << std::endl;
                std::cout << boost::format("Timed command: Setting Rx LO Offset: %f MHz...") 
                        % (rx_lo_offset / 1e6) << std::endl;
            }


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
            if (round == 0){
                std::cout << std::endl;
                std::cout << boost::format("Actual Rx Freq: %f MHz...")
                                % (rx_usrp->get_rx_freq(channel) / 1e6)
                        << std::endl;
                std::cout << "----------------------------" <<std::endl;
            }


            // set the rf gain (always has default value)
            if (round == 0){
                std::cout << std::endl;
                std::cout << std::endl;
                std::cout << boost::format("Setting Rx Gain: %f dB...") % rx_gain << std::endl;
            }

            rx_usrp->set_rx_gain(rx_gain, channel);

            if (round == 0){
                std::cout << boost::format("Actual Rx Gain: %f dB...")
                                % rx_usrp->get_rx_gain(channel)
                        << std::endl;
            }


            // set the analog frontend filter bandwidth

            if (vm.count("rx-bw")) {
                if (round == 0){
                    std::cout << std::endl;
                    std::cout << boost::format("Setting Rx Bandwidth: %f MHz...") % (rx_bw / 1e6)
                            << std::endl;
                }

                rx_usrp->set_rx_bandwidth(rx_bw, channel);

                if (round == 0){
                    std::cout << boost::format("Actual Rx Bandwidth: %f MHz...")
                                    % rx_usrp->get_rx_bandwidth(channel / 1e6)
                            << std::endl;
                }
            }

            // set the antenna (always has default value)
            rx_usrp->set_rx_antenna(rx_ant, channel);
        }



    //// ====== Wait for Setup ======
        std::this_thread::sleep_for(std::chrono::seconds(int64_t(1 * setup_time))); // allow for some setup time



    //// ====== Pre-compute wavetable ======
        if (round == 0)
            signal_file = signal_file + ".txt";
        
        const wave_table_class_Brian wave_table_Brian(wave_type, ampl, signal_file);
        const size_t step = 1;
        size_t index = 0;



    //// ====== Create a transmit streamer ======
        // linearly map channels (index0 = channel0, index1 = channel1, ...)
        uhd::stream_args_t tx_stream_args("fc32", wirefmt);
        tx_stream_args.channels = tx_channel_nums;
        uhd::tx_streamer::sptr tx_stream = tx_usrp->get_tx_stream(tx_stream_args);



    //// ====== Allocate a buffer which we re-use for each channel ======
        if (spb == 0) 
            spb = tx_stream->get_max_num_samps() * 10;
        std::vector<std::complex<float>> tx_buff(spb);
        int tx_size_channels = tx_channel_nums.size();  // not sure what it is
        // std::vector<std::complex<float>*> buffs(tx_size_channels, &tx_buff.front());
    


    // //// ====== Pre-fill the buffer ======
    //     std::cout<<"size of Tx buffer is: "<<tx_buff.size()<<" and step is: " << step << std::endl;
    //     for (size_t n = 0; n < tx_buff.size(); n++) 
    //         tx_buff[n] = wave_table(index += step);


    
    //// ====== Check Ref and LO Lock detect ======
        // LO locking check
        std::vector<std::string> tx_sensor_names, rx_sensor_names;
        const size_t tx_sensor_chan = tx_channel_nums.empty() ? 0 : tx_channel_nums[0];   // in this case, the value is still 0
        tx_sensor_names = tx_usrp->get_tx_sensor_names(tx_sensor_chan);

        if (std::find(tx_sensor_names.begin(), tx_sensor_names.end(), "lo_locked")
            != tx_sensor_names.end()) {
            uhd::sensor_value_t lo_locked = tx_usrp->get_tx_sensor("lo_locked", tx_sensor_chan);
            std::cout << std::endl;
            std::cout << boost::format("Checking Tx: %s ...") % lo_locked.to_pp_string()
                    << std::endl;
            UHD_ASSERT_THROW(lo_locked.to_bool());
        }

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


        // Reference Clock
        tx_sensor_names = tx_usrp->get_mboard_sensor_names(0);
        if ((ref == "external")
            and (std::find(tx_sensor_names.begin(), tx_sensor_names.end(), "ref_locked")
                    != tx_sensor_names.end())) {
            uhd::sensor_value_t ref_locked = tx_usrp->get_mboard_sensor("ref_locked", 0);
            std::cout << std::endl;
            std::cout << boost::format("Checking Tx: %s ...") % ref_locked.to_pp_string()
                    << std::endl;
            UHD_ASSERT_THROW(ref_locked.to_bool());
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



    //// ====== Set up metadata ======
        uhd::tx_metadata_t tx_md;
        tx_md.start_of_burst = true;
        tx_md.end_of_burst   = false;
        tx_md.has_time_spec  = true;
        tx_md.time_spec      = uhd::time_spec_t(tx_start); // test if the Tx will not send until t = 10. 
        long long tx_starting_tick = tx_md.time_spec.to_ticks(200e6);
        double tx_starting_sec = tx_md.time_spec.get_real_secs();

        if (round == 0){
            std::cout << std::endl;
            std::cout << std::endl;
            std::cout << "Tx: Wait for less than " << tx_md.time_spec.get_real_secs() << " seconds to start streaming..."
                    << std::endl;

            std::cout << std::endl;
            std::cout << "Tx Metadata Here... " << std::endl;
            std::cout << "  Streaming starting tick = " << tx_starting_tick << std::endl;
            std::cout << "  Streaming starting sec = " << tx_starting_sec 
                        << std::endl;
        }

        



    //// ====== Streaming prints ======
        if (total_num_samps == 0) {
            std::signal(SIGINT, &sig_int_handler);
            std::cout << "Press Ctrl + C to stop streaming..." << std::endl;
        }



    //// ====== File Naming ======
        char full_file_name[200];
        char full_rx_metafile_name[200];
        char full_tx_metafile_name[200];
        std::string data_file_group_str = std::to_string(data_file_group);
        std::string testid_str = std::to_string(data_file_testid);
        strcpy(full_file_name, data_file.c_str());  // test_
        strcat(full_file_name, data_file_group_str.c_str());  // test_1
        strcat(full_file_name, "_");    // test_1_
        strcat(full_file_name, testid_str.c_str());     //test_1_5
        strcpy(full_rx_metafile_name, full_file_name);
        strcpy(full_tx_metafile_name, full_file_name);

        strcat(full_file_name, ".dat"); //test_1_5.dat
        strcat(full_rx_metafile_name, "_rx_metadata.dat"); //test_1_5_rx_metadata.dat
        strcat(full_tx_metafile_name, "_tx_metadata.dat"); //test_1_5_tx_metadata.dat
    
    
    
    //// ====== Start Tx ======
        boost::thread_group transmit_thread;
        transmit_thread.create_thread(boost::bind(
            &transmit_worker, tx_buff, wave_table_Brian, tx_stream, tx_md, step, index, tx_size_channels));

        

    //// ====== Start Rx ======
        recv_to_file<std::complex<double>>(
            rx_usrp, "fc64", wirefmt, full_file_name, full_rx_metafile_name, spb, \
            total_num_samps, total_time, rx_start, bw_summary, stats, null, enable_size_map, \
            continue_on_bad_packet, rx_channel_nums, round);



    //// ====== Save Tx Metadata ======
        
        
        
        if (not null){
            // strcpy(full_metafile_name, data_file.c_str());
            // strcat(full_metafile_name, "_tx_metadata.dat");
            tx_metadatafile_strm.open(full_tx_metafile_name, std::ofstream::binary);
            tx_metadatafile_strm.write((char*)&tx_starting_tick, sizeof(long long));
            tx_metadatafile_strm.close();


            std::cout << std::endl;
            std::cout << boost::format("Tx Metadata is saved in file: %s") % full_tx_metafile_name
                    << std::endl;
            std::cout << std::endl;
            std::cout << boost::format("Rx Metadata is saved in file: %s") % full_rx_metafile_name
                    << std::endl;
            std::cout << "===============================" << std::endl;
            std::cout << std::endl;

            std::cout << std::endl;
            std::cout<< "Both done!" <<std::endl;

        }


    // clean up transmit worker
    stop_signal_called = true;
    transmit_thread.join_all();



    data_file_testid++;

    if (round == data_file_N-1)
        std::this_thread::sleep_for(
                std::chrono::seconds(10)); // wait for stable?
}

    // finished
    return EXIT_SUCCESS;
}
