//
// Copyright 2011-2012,2014 Ettus Research LLC
// Copyright 2018 Ettus Research, a National Instruments Company
//
// SPDX-License-Identifier: GPL-3.0-or-later
//
//
// Modifier: Yuning (Brian) Zhang
// Copyright: 2023
//
// Sub-Modifier: Tyler Chen ~ 2023

// doc strings example
// https://developer.lsst.io/cpp/api-docs.html


/**********************************************
This code will be used as the Tx 
(USRP 2974) for the indoor experiment. 

USRP-2974 is the equivalent to a USRP X310 with two UBX-160 boards, a GPSDO and an onboard Intel i7 computer.

USRP Configuration reference: https://files.ettus.com/manual/page_usrp_x3x0.html
RF Configuration reference: https://files.ettus.com/manual/classuhd_1_1usrp_1_1multi__usrp.html
**********************************************/


/*------------------------------------
Notes:
    1. USRP Interface should be set to 10 Gigabit Ethernet - makes max sampling rate as 200MS/s (https://kb.ettus.com/About_USRP_Bandwidths_and_Sampling_Rates)
------------------------------------*/



/*=========================================
Items waited to be implemented:
    1. Integrate Python as a library into C++
        - https://www.codeproject.com/Articles/820116/Embedding-Python-program-in-a-C-Cplusplus-code
    2. Automation logic for indoor experiment
    3. RF configuration block - pack as a subfunction or whatever to make
        the main code as simple as possible
Question:
    1. What is the difference between ant/channels/subdev?
    2. How to make the send buffer size as equal to the txt file length?
        6/10/23 - what does this mean? The size of txt file like how may words in the text file?

    #include <iostream>
    #include <fstream>
    #include <string>

    using namespace std;

    const char FileName[] = "text.txt";

    int main () 
    {
    string line;
    ifstream inMyStream (FileName); 
    int c = 0;

    if (inMyStream.is_open()) 
    {

        while( getline ( inMyStream, line ) )
        {
            cout << line << endl;
            c += line.length();
        }
    }
        }
        inMyStream.close(); 

    system("pause");
    return 0;
    }

=========================================*/

/*=========================================
Thoughts:
    6/9/23 - library of python scripts to move the xy tables

=========================================*/
/*=========================================
Miles Stone Notes
6/9/13

    Now here are some questions to you who work on the coding part: 
    What is the difference between ant/channels/subdev?
    How to make the send buffer size as equal to the txt file length?

6/11/23

    Some tips about this issue: maybe you can try to load their example image, 
    select one of those predefined with UHD installed. 

    Haoyu working on cpp/python library integration 
    And for some tasks such as integrating Python into C++, you can also try to do it locally. 
    For example, write a small Python program, then try tointegrate it into another very simple C++ code and run it. 
    The functional part of the python/C++ code is not the point of this integration, 
    but how to configure the environment and how to insert Python into C++ is the key. 

    For tasks such as the rf coding, we need to figure out what are those parameters and what do they represent.
    For this part we need a huge amount of online searches and investigation which might don't need to even access the node as well. 

    For any final verification that has to do with the actual node, then it makes sense that you need to work with an image. 
    Still, if the one I created doesn't work/load, go from their prepared images and that should be working. 
    Notify me if their pre-provided image still doesn't work and then I'll send another request to COSMOS for urgent reaction. 
=========================================*/
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

/**
 * Sum numbers in a vector.
 *
 * @param takes an int 
 * @return no return
 */
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
    //// ====== Setup Variables ======
        //constant variables
        /* --- Timing configuration ---
        Reference: 
            1 PPS: https://files.ettus.com/manual/classuhd_1_1usrp_1_1multi__usrp.html#a57a5580ba06d7d6a037c9ef64f1ea361
            Ref: https://files.ettus.com/manual/classuhd_1_1usrp_1_1multi__usrp.html#a73ed40009d0d3787c183d42423d25026
        */
        const std::string pps = "external";
        const std::string ref = "external";
        
        /* --- RF configuration --- */
        const double rate = 200e6;  // Tx sampling rate, in Samples/sec
        const double bw = 100e6;    // Transmission bandwidth, in Hz
        const double freq = 3e9;    // 1st-stage IF center frequency, in Hz, should be 3 GHz. Then PAAM will keep UPC from 3 GHz to 28 GHz. 
    

        // variables to be set by po
        std::string args, file, ant, subdev, channel_list;
        size_t spb;
        double gain;
        
        po::options_description desc("Allowed options");    // setup the program options
        desc.add_options()
            ("help", "help message")

            /*
            For USRP 2974, RF0 - Tx(H)+Rx(H); RF1 - Tx(V)+Rx(V).
            Most likely, the subdev should be: B:0
            Refer to: https://files.ettus.com/manual/page_dboards.html#dboards_ubx

            set "args" as USRP's address
            Refer to: https://files.ettus.com/manual/page_usrp_x3x0.html#x3x0_usage_device_args
            */
            ("ant", po::value<std::string>(&ant)->default_value("AB"), "antenna selection")
            ("channels", po::value<std::string>(&channel_list)->default_value("0"), "which channels to use (specify \"0\", \"1\", \"0,1\", etc)")
            ("subdev", po::value<std::string>(&subdev)->default_value("A:AB"), "subdevice specification")
            ("args", po::value<std::string>(&args)->default_value("addr=10.37.21.1"), "USRP addresses, default is for the portable node mob4")

            // RF parameters
            ("gain", po::value<double>(&gain)->default_value(0), "gain for the Tx USRP")
            ("int-n", "tune USRP with integer-n tuning")

            // sounding signal/transmission
            ("file", po::value<std::string>(&file)->default_value(""), "name of the file to read binary samples from")
            ("spb", po::value<size_t>(&spb)->default_value(10000), "samples per buffer")  
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



    //// ====== Create a usrp device ======
        std::cout << std::endl;
        std::cout << boost::format("Creating the usrp device with: %s...") % args
                << std::endl;
        // uhd is defined at "<uhd/usrp/multi_usrp.hpp>"   
        uhd::usrp::multi_usrp::sptr usrp = uhd::usrp::multi_usrp::make(args);



    //// ====== Select Sub-device (always use default value) ======
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
            uhd::tune_request_t tune_request(freq);
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


    //// ************ copied from test_pps_input *********************
        // set the time at an unknown pps (will throw if no pps)
        std::cout << std::endl
                << "Attempt to detect the PPS and set the time..." << std::endl
                << std::endl;
        usrp->set_time_unknown_pps(uhd::time_spec_t(0.0));
        std::cout << std::endl << "Success!" << std::endl << std::endl;

        if (product_requires_reflock(usrp->get_mboard_name())) {
            std::cout << "Product requires verification of ref_locked sensor!" << std::endl;
            std::cout << "Checking ref_locked sensor..." << std::flush;
            if (!usrp->get_mboard_sensor("ref_locked").to_bool()) {
                std::cout << "FAIL!" << std::endl;
                return EXIT_FAILURE;
            }
            std::cout << "PASS!" << std::endl;
        }



    //// ====== Set sigint if user wants to receive ======
        std::signal(SIGINT, &sig_int_handler);
        std::cout << "Press Ctrl + C to stop streaming..." << std::endl;



    //// ====== Create a transmit streamer ======
        // refer to: https://files.ettus.com/manual/page_configuration.html#config_stream_args_cpu_format
        std::string cpu_format = "f32"; // Single-precision 32-bit data
        std::string wirefmt = "s16"; // Signed 16-bit integer data
        uhd::stream_args_t stream_args(cpu_format, wirefmt);
        channel_nums.push_back(boost::lexical_cast<size_t>(channel_list));
        stream_args.channels             = channel_nums;
        uhd::tx_streamer::sptr tx_stream = usrp->get_tx_stream(stream_args);



    //// ====== Continuosly Send data ======
        do {
            send_from_file<float>(tx_stream, file, spb);
        } while (not stop_signal_called);



    //// finished
        std::cout << std::endl << "Done!" << std::endl << std::endl;
        return EXIT_SUCCESS;
}
