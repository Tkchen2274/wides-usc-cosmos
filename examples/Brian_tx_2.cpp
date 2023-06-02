//
// Copyright 2010-2012,2014 Ettus Research LLC
// Copyright 2018 Ettus Research, a National Instruments Company
//
// SPDX-License-Identifier: GPL-3.0-or-later
//

#include "wavetable_Brian.hpp"
// #include "wavetable.hpp"
#include <uhd/exception.hpp>
#include <uhd/usrp/multi_usrp.hpp>
#include <uhd/utils/safe_main.hpp>
#include <uhd/utils/static.hpp>
#include <uhd/utils/thread.hpp>
#include <stdint.h>
#include <boost/algorithm/string.hpp>
#include <boost/format.hpp>
#include <boost/math/special_functions/round.hpp>
#include <boost/program_options.hpp>
#include <boost/algorithm/string.hpp>
#include <chrono>
#include <csignal>
#include <iostream>
#include <string>
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
 * Main function
 **********************************************************************/
int UHD_SAFE_MAIN(int argc, char* argv[])
{
    // variables to be set by po
    std::string tx_args, wave_type, tx_ant, tx_subdev, ref, pps, wirefmt, tx_channels, signal_file;
    // uint64_t total_num_samps;
    size_t spb;
    double tx_rate, freq, tx_gain, tx_bw, tx_lo_offset, tx_start, setup_time;
    float ampl;
    // float T0 = 1e-6;
    // double wave_freq, max_freq;
    

    // setup the program options
    po::options_description desc("Allowed options");
    // clang-format off
    desc.add_options()
        ("help", "help message")

        ("tx-ant", po::value<std::string>(&tx_ant)->default_value("AB"), "antenna selection")
        ("tx-args", po::value<std::string>(&tx_args)->default_value("addr=10.38.14.1"), 
            "single uhd device address args, and it can be IP address. Default value is the Tx USRP. ")
        ("tx-bw", po::value<double>(&tx_bw), "analog frontend filter bandwidth in Hz")
        ("tx-channels", po::value<std::string>(&tx_channels)->default_value("0"), "which channels to use (specify \"0\", \"1\", \"0,1\", etc)")
        ("tx-gain", po::value<double>(&tx_gain)->default_value(0), "gain for the RF chain")
        ("tx-int-n", "tune USRP with integer-N tuning")
        ("tx-lo-offset", po::value<double>(&tx_lo_offset)->default_value(0.0),
            "Offset for frontend LO in Hz (optional)")    
        ("tx-rate", po::value<double>(&tx_rate)->default_value(200e6), "rate of outgoing samples")
        ("tx-signal", po::value<std::string>(&signal_file)->default_value("cosmos_-100MHz_to_100MHz_SR_200MS"), "signal txt file name")
        ("tx-start", po::value<double>(&tx_start)->default_value(5.0), "start streaming time")
        ("tx-subdev", po::value<std::string>(&tx_subdev)->default_value("A:AB"), "subdevice specification, use A:AB for Tx")
        
        ("ampl", po::value<float>(&ampl)->default_value(float(1)), "amplitude of the waveform [0 to 0.7]")
        ("freq", po::value<double>(&freq)->default_value(100e6), "IF center frequency in Hz")
        ("pps", po::value<std::string>(&pps)->default_value("external"), "PPS source (internal, external, mimo, gpsdo)")
        ("ref", po::value<std::string>(&ref)->default_value("external"), "clock reference (internal, external, mimo, gpsdo)")
        ("setup", po::value<double>(&setup_time)->default_value(1.0), "seconds of setup time")
        ("spb", po::value<size_t>(&spb)->default_value(0), "samples per buffer, 0 for default")
        ("wave-type", po::value<std::string>(&wave_type)->default_value("OFDM"), "waveform type (SINE)")
        ("wirefmt", po::value<std::string>(&wirefmt)->default_value("sc16"), "specify the over-the-wire sample mode")

    ;
    
    //// ====== Clang-format on ======
        // An object of class "variables_map" is declared. That class is intended to store values 
        // of options, and can store values of arbitrary types. Next, the calls to "store", 
        // "parse_command_line" and "notify" functions cause "vm" to contain all the options found 
        // on the command line.
        //
        // If an option "arg" exists, then "vm.count(arg)" returns a bool value to represent True. 
        // 
        po::variables_map vm;
        po::store(po::parse_command_line(argc, argv, desc), vm);
        po::notify(vm);

    
    
    //// ====== Print the help message ======
        if (vm.count("help")) {
            std::cout << boost::format("UHD Tx sending OFDM by WiDeS %s") % desc << std::endl;
            return ~0;
        }



    //// ====== Create a usrp device ======
        std::cout << std::endl;
        std::cout << boost::format("Creating the usrp device with: %s...") % tx_args
                << std::endl;
        // uhd is defined at "<uhd/usrp/multi_usrp.hpp>" and implemented in "uhd/lib/.cpp"   
        uhd::usrp::multi_usrp::sptr tx_usrp = uhd::usrp::multi_usrp::make(tx_args);



    //// ====== Select Sub-device (always has default value) ======
        tx_usrp->set_tx_subdev_spec(tx_subdev);   // A:AB for Tx, and B:AB for Rx, check the "X310 probe" note in Samsung Notes



    //// ====== Print Device Info ======
        // "get_pp_string" will return:
        //  1. USRP clock device;
        //  2. board amount, and their references;
        std::cout << std::endl;
        std::cout << boost::format("Using TX Device: %s") % tx_usrp->get_pp_string()
                << std::endl;
        


    //// ====== Detect which channels to use ======
        // if build error: split is not member of boost, then add library:
        // #include <boost/algorithm/string.hpp>
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



    //// ====== Set mboard reference clock source (always has default value) ======
        tx_usrp->set_clock_source(ref);

        std::cout << std::endl;
        std::cout<<boost::format("The reference clock for the Tx is: %s...") % ref
                    <<std::endl;



    //// ====== Reset timestamp and pps (always has default value) ======
        std::cout << boost::format("Setting device timestamp to 0 for the next unknown PPS edge...") << std::endl;

        tx_usrp->set_time_source(pps);

        tx_usrp->set_time_unknown_pps(uhd::time_spec_t(0.0));  // set the next coming pps as t = 0;
        std::this_thread::sleep_for(
            std::chrono::milliseconds(200)); // wait for pps sync pulse
        std::cout << "Current Tx time is: " << tx_usrp->get_time_now(0).get_real_secs() << std::endl;
        
        std::cout<<std::endl;
        std::cout<<"t=0 timestamp set."
            <<std::endl;   



    //// ====== Set the sample rate (always has default value) ======
        // set the Tx sample rate
        std::cout << boost::format("Setting Tx Rate: %f Msps...") % (tx_rate / 1e6) << std::endl;
        tx_usrp->set_tx_rate(tx_rate);  // remove the channels parameters or not?
        std::cout << boost::format("Actual Tx Rate: %f Msps...")
                        % (tx_usrp->get_tx_rate() / 1e6)
                << std::endl;
                


    //// ====== Configure each channel ======
        for (size_t ch_idx = 0; ch_idx < tx_channel_nums.size(); ch_idx++) {

            size_t channel = tx_channel_nums[ch_idx];

            std::cout << std::endl;
            std::cout << std::endl;
            std::cout << "----------------------------" <<std::endl;
            std::cout << boost::format("Timed command: Setting Tx Freq: %f MHz...") 
                    % (freq / 1e6) << std::endl;
            std::cout << boost::format("Timed command: Setting Tx LO Offset: %f MHz...") 
                    % (tx_lo_offset / 1e6) << std::endl;

            // start timed command with tune: 
            tx_usrp->clear_command_time();
            tx_usrp->set_command_time(uhd::time_spec_t(4.0));  //operate any command after "set_command_time" at t sec;
            
            // timed command content:
                uhd::tune_request_t tx_tune_request(freq, tx_lo_offset);
                if (vm.count("int-n"))
                    tx_tune_request.args = uhd::device_addr_t("mode_n=integer");
                tx_usrp->set_tx_freq(tx_tune_request, channel);
                std::this_thread::sleep_for(std::chrono::milliseconds(110)); //sleep 110ms (~10ms after retune occurs) to allow LO to lock

            tx_usrp->clear_command_time();


            // print setting results
            std::cout << std::endl;
            std::cout << boost::format("Actual Tx Freq: %f MHz...")
                            % (tx_usrp->get_tx_freq(channel) / 1e6)
                    << std::endl;
                    


            // set the rf gain (always has default value)
            std::cout<<std::endl;
            std::cout << boost::format("Setting Tx Gain: %f dB...") % tx_gain << std::endl;
            tx_usrp->set_tx_gain(tx_gain, channel);
            std::cout << boost::format("Actual Tx Gain: %f dB...")
                            % tx_usrp->get_tx_gain(channel)
                    << std::endl;
                    


            // set the analog frontend filter bandwidth
            if (vm.count("tx-bw")) {
                std::cout<<std::endl;
                std::cout << boost::format("Setting Tx Bandwidth: %f MHz...") % (tx_bw / 1e6)
                        << std::endl;
                tx_usrp->set_tx_bandwidth(tx_bw, channel);
                std::cout << boost::format("Actual Tx Bandwidth: %f MHz...")
                                % tx_usrp->get_tx_bandwidth(channel / 1e6)
                        << std::endl;
            }


            // set the antenna (always has default value)
            tx_usrp->set_tx_antenna(tx_ant, channel);
        }



    //// ====== Wait for Setup ======
        std::this_thread::sleep_for(std::chrono::seconds(int64_t(1 * setup_time))); // allow for some setup time



    //// ====== Pre-compute wavetable ======
        signal_file = signal_file + ".txt";
        const wave_table_class_Brian wave_table_Brian(wave_type, ampl, signal_file);
        const size_t step = 1;
        size_t index = 0;



    //// ====== Create a transmit streamer ======
        // linearly map channels (index0 = channel0, index1 = channel1, ...)
        uhd::stream_args_t tx_stream_args("fc32", wirefmt);
        tx_stream_args.channels             = tx_channel_nums;
        uhd::tx_streamer::sptr tx_stream = tx_usrp->get_tx_stream(tx_stream_args);



    //// ====== Allocate a buffer which we re-use for each channel ======
        if (spb == 0) 
            spb = tx_stream->get_max_num_samps() * 10;
        std::vector<std::complex<float>> tx_buff(spb);
        int tx_size_channels = tx_channel_nums.size();  // not sure what it is
        

        
    // //// ====== Pre-fill the buffer ======
    //     std::cout<<"size of buffer is: "<<tx_buff.size()<<" and step is: " << step << std::endl;
    //     for (size_t n = 0; n < tx_buff.size(); n++) 
    //         tx_buff[n] = wave_table_Brian(index += step);




    


    

    //// ====== Check Ref and LO Lock detect ======
        // LO locking check
        std::vector<std::string> tx_sensor_names;
        const size_t tx_sensor_chan = tx_channel_nums.empty() ? 0 : tx_channel_nums[0];   // in this case, the value is still 0
        tx_sensor_names = tx_usrp->get_tx_sensor_names(tx_sensor_chan);

        if (std::find(tx_sensor_names.begin(), tx_sensor_names.end(), "lo_locked")
            != tx_sensor_names.end()) {
            uhd::sensor_value_t lo_locked = tx_usrp->get_tx_sensor("lo_locked", tx_sensor_chan);
            std::cout << boost::format("Checking Tx: %s ...") % lo_locked.to_pp_string()
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



    //// ====== Set up metadata ======
        uhd::tx_metadata_t tx_md;
        tx_md.start_of_burst = true;
        tx_md.end_of_burst   = false;
        tx_md.has_time_spec  = true;
        tx_md.time_spec      = uhd::time_spec_t(tx_start); // test if the Tx will not send until t = 10. 
        long long tx_starting_tick = tx_md.time_spec.to_ticks(200e6);
        double tx_starting_sec = tx_md.time_spec.get_real_secs();

        std::cout << std::endl;
        std::cout << std::endl;
        std::cout << "Tx: Wait for less than " << tx_md.time_spec.get_real_secs() << " seconds to start streaming..."
                << std::endl;

        std::cout << std::endl;
        std::cout << "Tx Metadata Here... " << std::endl;
        std::cout << "  Streaming starting tick = " << tx_starting_tick << std::endl;
        std::cout << "  Streaming starting sec = " << tx_starting_sec 
                    << std::endl;



    //// ====== Streaming prints ======
        std::signal(SIGINT, &sig_int_handler);
        std::cout << "Press Ctrl + C to stop streaming..." << std::endl << std::endl;
    


    //// ====== Send data ======
        // Until the signal handler gets called or if we accumulate the number 
        // of samples that been specified (unless it's 0).
        std::vector<std::complex<float>*> buffs(tx_size_channels, &tx_buff.front());
        uhd::set_thread_priority(); //Added as suggested by Neel
        while (not stop_signal_called) {
            // fill the buffer with the waveform
            for (size_t n = 0; n < tx_buff.size(); n++) {
                tx_buff[n] = wave_table_Brian(index += step);
            }

            // send the entire contents of the buffer
            tx_stream->send(buffs, tx_buff.size(), tx_md);

            tx_md.start_of_burst = false;
            tx_md.has_time_spec  = false;
        }

        // send a mini EOB packet
        tx_md.end_of_burst = true;
        tx_stream->send("", 0, tx_md);



    //// finished
        // "EXIT_SUCCESS" and "0" both mean the program has executed successfully, 
        // but "EXIT_SUCCESS" is not requried to be equal to 0.
        std::cout << std::endl << "Done!" << std::endl << std::endl;

        return EXIT_SUCCESS;
}

