//
// Copyright 2011-2012,2014 Ettus Research LLC
// Copyright 2018 Ettus Research, a National Instruments Company
//
// SPDX-License-Identifier: GPL-3.0-or-later
//

#include <uhd/types/tune_request.hpp>
#include <uhd/usrp/multi_usrp.hpp>
#include <uhd/utils/safe_main.hpp>
#include <uhd/utils/thread.hpp>
#include <boost/format.hpp>
#include <boost/program_options.hpp>
#include <boost/math/special_functions/round.hpp>
#include <boost/program_options.hpp>
#include <boost/algorithm/string.hpp>   // boost::split
#include <chrono>
#include <complex>
#include <csignal>
#include <fstream>
#include <iostream>
#include <thread>

namespace po = boost::program_options;

static bool stop_signal_called = false;
void sig_int_handler(int)
{
    stop_signal_called = true;
}

template <typename samp_type>
void send_from_file(
    uhd::tx_streamer::sptr tx_stream, const std::string& file, size_t samps_per_buff)
{
    uhd::tx_metadata_t md;
    md.start_of_burst = false;
    md.end_of_burst   = false;
    std::vector<samp_type> buff(samps_per_buff);
    std::ifstream infile(file.c_str(), std::ifstream::binary);

    // loop until the entire file has been read

    while (not md.end_of_burst and not stop_signal_called) {
        infile.read((char*)&buff.front(), buff.size() * sizeof(samp_type));
        size_t num_tx_samps = size_t(infile.gcount() / sizeof(samp_type));

        md.end_of_burst = infile.eof();

        tx_stream->send(&buff.front(), num_tx_samps, md);
    }

    infile.close();
}

int UHD_SAFE_MAIN(int argc, char* argv[])
{
    // variables to be set by po
    std::string args, file, type, ant, subdev, ref, pps, wirefmt, channel_list;
    size_t spb;
    double rate, freq, gain, bw, delay, lo_offset;

    // setup the program options
    po::options_description desc("Allowed options");
    // clang-format off
    desc.add_options()
        // ("help", "help message")
        // ("args", po::value<std::string>(&args)->default_value(""), "multi uhd device address args")
        // ("file", po::value<std::string>(&file)->default_value("usrp_samples.dat"), "name of the file to read binary samples from")
        // ("type", po::value<std::string>(&type)->default_value("short"), "sample type: double, float, or short")
        // ("spb", po::value<size_t>(&spb)->default_value(10000), "samples per buffer")
        // ("rate", po::value<double>(&rate), "rate of outgoing samples")
        // ("freq", po::value<double>(&freq), "RF center frequency in Hz")
        // ("lo-offset", po::value<double>(&lo_offset)->default_value(0.0),
        //     "Offset for frontend LO in Hz (optional)")
        // ("lo_off", po::value<double>(&lo_offset),
        //     "(DEPRECATED) will go away soon! Use --lo-offset instead")
        // ("gain", po::value<double>(&gain), "gain for the RF chain")
        // ("ant", po::value<std::string>(&ant), "antenna selection")
        // ("subdev", po::value<std::string>(&subdev), "subdevice specification")
        // ("bw", po::value<double>(&bw), "analog frontend filter bandwidth in Hz")
        // ("ref", po::value<std::string>(&ref)->default_value("internal"), "reference source (internal, external, mimo)")
        // ("wirefmt", po::value<std::string>(&wirefmt)->default_value("sc16"), "wire format (sc8 or sc16)")
        // ("delay", po::value<double>(&delay)->default_value(0.0), "specify a delay between repeated transmission of file (in seconds)")
        // ("channel", po::value<std::string>(&channel)->default_value("0"), "which channel to use")
        // ("repeat", "repeatedly transmit file")
        // ("int-n", "tune USRP with integer-n tuning")


        ("help", "help message")

        ("ant", po::value<std::string>(&ant)->default_value("AB"), "antenna selection")
        ("args", po::value<std::string>(&args)->default_value("addr=10.38.14.1"), "multi uhd device address args")
        ("bw", po::value<double>(&bw), "analog frontend filter bandwidth in Hz")
        ("channels", po::value<std::string>(&channel_list)->default_value("0"), "which channels to use (specify \"0\", \"1\", \"0,1\", etc)")
        ("delay", po::value<double>(&delay)->default_value(0.0), "specify a delay between repeated transmission of file (in seconds)")
        ("file", po::value<std::string>(&file)->default_value(""), "name of the file to read binary samples from")
        ("freq", po::value<double>(&freq)->default_value(80e6), "RF center frequency in Hz")
        ("gain", po::value<double>(&gain)->default_value(0), "gain for the RF chain")
        ("int-n", "tune USRP with integer-n tuning")
        ("lo-offset", po::value<double>(&lo_offset)->default_value(0.0),
            "Offset for frontend LO in Hz (optional)")
        ("pps", po::value<std::string>(&pps)->default_value("external"), "PPS source (internal, external, mimo, gpsdo)")
        ("rate", po::value<double>(&rate)->default_value(10e6), "rate of outgoing samples")
        ("ref", po::value<std::string>(&ref)->default_value("external"), "reference source (internal, external, mimo)")
        ("onetime", "NOT repeatedly transmit file, only transmit for onetime only")
        ("spb", po::value<size_t>(&spb)->default_value(10000), "samples per buffer")
        ("subdev", po::value<std::string>(&subdev)->default_value("A:AB"), "subdevice specification")
        ("type", po::value<std::string>(&type)->default_value("double"), "sample type: double, float, or short")
        ("wirefmt", po::value<std::string>(&wirefmt)->default_value("sc16"), "wire format (sc8 or sc16)")    
        

        
    ;
    //// ====== Clang-format on ======
        po::variables_map vm;
        po::store(po::parse_command_line(argc, argv, desc), vm);
        po::notify(vm);



    //// ====== Print the help message ======
        if (vm.count("help")) {
            std::cout << boost::format("UHD TX samples from file %s") % desc << std::endl;
            return ~0;
        }



    //// ====== Set transmission mode, repeatedly or onetime only ======
        bool onetime = vm.count("onetime") > 0;



    //// ====== Create a usrp device ======
        std::cout << std::endl;
        std::cout << boost::format("Creating the usrp device with: %s...") % args
                << std::endl;
        // uhd is defined at "<uhd/usrp/multi_usrp.hpp>"   
        uhd::usrp::multi_usrp::sptr usrp = uhd::usrp::multi_usrp::make(args);



    //// ====== Select Sub-device (always has default value) ======
        if (vm.count("subdev"))
            usrp->set_tx_subdev_spec(subdev);  // A:AB for Tx, and B:AB for Rx, check the "X310 probe" note in Samsung Notes
    
    

    //// ====== Detect which channels to use ======
        std::vector<std::string> channel_strings;
        std::vector<size_t> channel_nums;
        boost::split(channel_strings, channel_list, boost::is_any_of("\"',"));
        for (size_t ch_idx = 0; ch_idx < channel_strings.size(); ch_idx++) {
            size_t chan = std::stoi(channel_strings[ch_idx]);
            if (chan >= usrp->get_tx_num_channels())
                throw std::runtime_error("Invalid channel(s) specified.");
            else
                channel_nums.push_back(std::stoi(channel_strings[ch_idx]));
        }

    
    
    //// ====== Lock mboard reference clock source (always has default value) ======
        usrp->set_clock_source(ref);
        std::cout<<boost::format("The reference clock for motherboard is: %s...") % ref
                    <<std::endl;



    //// ====== Print Device Info ======
        // "get_pp_string" will return:
        //  1. USRP clock device;
        //  2. board amount, and their references;
        std::cout << boost::format("Using Device: %s") % usrp->get_pp_string() << std::endl;



    //// ====== Set the sample rate ======
        if (not vm.count("rate")) {
            std::cerr << "Please specify the sample rate with --rate" << std::endl;
            return ~0;
        }
        std::cout << boost::format("Setting TX Rate: %f Msps...") % (rate / 1e6) << std::endl;
        usrp->set_tx_rate(rate);
        std::cout << boost::format("Actual TX Rate: %f Msps...") % (usrp->get_tx_rate() / 1e6)
                << std::endl;



    //// ====== Set the center frequency (always has default value) ======
            // std::cerr << "Please specify the center frequency with --freq" << std::endl;
            // return ~0;



    //// ====== Configure each channel ======
        for (size_t ch_idx = 0; ch_idx < channel_nums.size(); ch_idx++) {
            std::cout << boost::format("Setting TX Freq: %f MHz...") % (freq / 1e6) 
                    << std::endl;
            std::cout << boost::format("Setting TX LO Offset: %f MHz...") % (lo_offset / 1e6)
                    << std::endl;
            uhd::tune_request_t tune_request(freq, lo_offset);
            // tune_request = uhd::tune_request_t(freq, lo_offset);
            if (vm.count("int-n"))
                tune_request.args = uhd::device_addr_t("mode_n=integer");
            usrp->set_tx_freq(tune_request, channel_nums[ch_idx]);
            std::cout << boost::format("Actual TX Freq: %f MHz...") 
                            % (usrp->get_tx_freq(channel_nums[ch_idx]) / 1e6)
                    << std::endl
                    << std::endl;

            // set the rf gain (always has default value)
                std::cout << boost::format("Setting TX Gain: %f dB...") % gain << std::endl;
                usrp->set_tx_gain(gain, channel_nums[ch_idx]);
                std::cout << boost::format("Actual TX Gain: %f dB...") 
                                % usrp->get_tx_gain(channel_nums[ch_idx])
                        << std::endl
                        << std::endl;
            

            // set the analog frontend filter bandwidth
            if (vm.count("bw")) {
                std::cout << boost::format("Setting TX Bandwidth: %f MHz...") % (bw / 1e6)
                        << std::endl;
                usrp->set_tx_bandwidth(bw, channel_nums[ch_idx]);
                std::cout << boost::format("Actual TX Bandwidth: %f MHz...")
                                % usrp->get_tx_bandwidth(channel_nums[ch_idx] / 1e6)
                        << std::endl
                        << std::endl;
            }


            // set the antenna
            if (vm.count("ant"))
                usrp->set_tx_antenna(ant, channel_nums[ch_idx]);
        }





    std::this_thread::sleep_for(std::chrono::seconds(1)); // allow for some setup time




    //// ====== Set timestamp and pps ======
        std::cout << boost::format("Setting device timestamp to 0...") << std::endl;
        std::cout << "channel num = " << channel_nums.size()<< std::endl;
        if (channel_nums.size() >= 1) {
            // Sync times
            if (pps == "mimo") {
                UHD_ASSERT_THROW(usrp->get_num_mboards() == 2);

                // make mboard 1 a slave over the MIMO Cable
                usrp->set_time_source("mimo", 1);

                // set time on the master (mboard 0)
                usrp->set_time_now(uhd::time_spec_t(0.0), 0);

                // sleep a bit while the slave locks its time to the master
                std::this_thread::sleep_for(std::chrono::milliseconds(100));
            } else {
                if (pps == "internal" or pps == "external" or pps == "gpsdo"){
                    usrp->set_time_source(pps);
                    std::cout<<"pps set success"<<std::endl;
                }
                usrp->set_time_unknown_pps(uhd::time_spec_t(0.0));
                std::this_thread::sleep_for(
                    std::chrono::seconds(1)); // wait for pps sync pulse
            }
        } else {
            usrp->set_time_now(0.0);
        }



    //// ====== Check Ref and LO Lock detect ======
        std::vector<std::string> sensor_names;
        const size_t tx_sensor_chan = channel_nums.empty() ? 0 : channel_nums[0];
        sensor_names                = usrp->get_tx_sensor_names(tx_sensor_chan);
        if (std::find(sensor_names.begin(), sensor_names.end(), "lo_locked")
            != sensor_names.end()) {
            uhd::sensor_value_t lo_locked = usrp->get_tx_sensor("lo_locked", tx_sensor_chan);
            std::cout << boost::format("Checking TX: %s ...") % lo_locked.to_pp_string()
                    << std::endl;
            UHD_ASSERT_THROW(lo_locked.to_bool());
        }
        const size_t mboard_sensor_idx = 0;
        sensor_names = usrp->get_mboard_sensor_names(mboard_sensor_idx);
        if ((ref == "mimo")
            and (std::find(sensor_names.begin(), sensor_names.end(), "mimo_locked")
                    != sensor_names.end())) {
            uhd::sensor_value_t mimo_locked =
                usrp->get_mboard_sensor("mimo_locked", mboard_sensor_idx);
            std::cout << boost::format("Checking TX: %s ...") % mimo_locked.to_pp_string()
                    << std::endl;
            UHD_ASSERT_THROW(mimo_locked.to_bool());
        }
        if ((ref == "external")
            and (std::find(sensor_names.begin(), sensor_names.end(), "ref_locked")
                    != sensor_names.end())) {
            uhd::sensor_value_t ref_locked =
                usrp->get_mboard_sensor("ref_locked", mboard_sensor_idx);
            std::cout << boost::format("Checking TX: %s ...") % ref_locked.to_pp_string()
                    << std::endl;
            UHD_ASSERT_THROW(ref_locked.to_bool());
        }



    //// ====== Set sigint if user wants to receive ======
        if (not onetime) {
            std::signal(SIGINT, &sig_int_handler);
            std::cout << "Press Ctrl + C to stop streaming..." << std::endl;
        }



    //// ====== Create a transmit streamer ======
        std::string cpu_format;
        if (type == "double")
            cpu_format = "fc64";
        else if (type == "float")
            cpu_format = "fc32";
        else if (type == "short")
            cpu_format = "sc16";
        uhd::stream_args_t stream_args(cpu_format, wirefmt);
        channel_nums.push_back(boost::lexical_cast<size_t>(channel_list));
        stream_args.channels             = channel_nums;
        uhd::tx_streamer::sptr tx_stream = usrp->get_tx_stream(stream_args);



    //// ====== Send data ======
        do {
            if (type == "double")
                send_from_file<std::complex<double>>(tx_stream, file, spb);
            else if (type == "float")
                send_from_file<std::complex<float>>(tx_stream, file, spb);
            else if (type == "short")
                send_from_file<std::complex<short>>(tx_stream, file, spb);
            else
                throw std::runtime_error("Unknown type " + type);

            if (not onetime and delay > 0.0) {
                std::this_thread::sleep_for(std::chrono::milliseconds(int64_t(delay * 1000)));
            }
        } while (not onetime and not stop_signal_called);



    //// finished
        std::cout << std::endl << "Done!" << std::endl << std::endl;
        return EXIT_SUCCESS;
}
