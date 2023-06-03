//
// Copyright 2010,2012,2014 Ettus Research LLC
// Copyright 2018 Ettus Research, a National Instruments Company
//
// SPDX-License-Identifier: GPL-3.0-or-later
//

#include "usrp_cal_utils.hpp"
#include <uhd/utils/safe_main.hpp>
#include <uhd/utils/thread.hpp>
#include <boost/math/special_functions/round.hpp>
#include <boost/program_options.hpp>
#include <boost/thread/thread.hpp>
#include <chrono>
#include <complex>
#include <cstdlib>
#include <ctime>
#include <iostream>
#include <thread>

namespace po = boost::program_options;

/***********************************************************************
 * Transmit thread
 **********************************************************************/
static void tx_thread(uhd::usrp::multi_usrp::sptr usrp,
    uhd::tx_streamer::sptr tx_stream,
    const double tx_wave_freq,
    const double tx_wave_ampl)
{
    uhd::set_thread_priority_safe();

    // set max TX gain
    usrp->set_tx_gain(usrp->get_tx_gain_range().stop());

    // setup variables and allocate buffer
    uhd::tx_metadata_t md;
    md.has_time_spec = false;
    std::vector<samp_type> buff(tx_stream->get_max_num_samps() * 10);

    // values for the wave table lookup
    size_t index         = 0;
    const double tx_rate = usrp->get_tx_rate();
    const size_t step    = boost::math::iround(wave_table_len * tx_wave_freq / tx_rate);
    wave_table table(tx_wave_ampl);

    // fill buff and send until interrupted
    while (not boost::this_thread::interruption_requested()) {
        for (size_t i = 0; i < buff.size(); i++)
            buff[i] = table(index += step);
        tx_stream->send(&buff.front(), buff.size(), md);
    }

    // send a mini EOB packet
    md.end_of_burst = true;
    tx_stream->send("", 0, md);
}

/***********************************************************************
 * Tune RX and TX routine
 **********************************************************************/
static double tune_rx_and_tx(
    uhd::usrp::multi_usrp::sptr usrp, const double tx_lo_freq, const double rx_offset)
{
    // tune the transmitter with no cordic
    uhd::tune_request_t tx_tune_req(tx_lo_freq);
    tx_tune_req.dsp_freq_policy = uhd::tune_request_t::POLICY_MANUAL;
    tx_tune_req.dsp_freq        = 0;
    usrp->set_tx_freq(tx_tune_req);

    // tune the receiver
    double rx_freq        = usrp->get_tx_freq() - rx_offset;
    double min_fe_rx_freq = usrp->get_fe_rx_freq_range().start();
    double max_fe_rx_freq = usrp->get_fe_rx_freq_range().stop();
    uhd::tune_request_t rx_tune_req(rx_freq);
    rx_tune_req.dsp_freq_policy = uhd::tune_request_t::POLICY_MANUAL;
    rx_tune_req.dsp_freq        = 0;
    if (rx_freq < min_fe_rx_freq)
        rx_tune_req.dsp_freq = rx_freq - min_fe_rx_freq;
    else if (rx_freq > max_fe_rx_freq)
        rx_tune_req.dsp_freq = rx_freq - max_fe_rx_freq;
    usrp->set_rx_freq(rx_tune_req);

    wait_for_lo_lock(usrp);

    return usrp->get_tx_freq();
}

/***********************************************************************
 * Main
 **********************************************************************/
int UHD_SAFE_MAIN(int argc, char* argv[])
{
    std::string args, subdev, serial;
    double tx_wave_freq, tx_wave_ampl, rx_offset;
    double freq_start, freq_stop, freq_step;
    size_t nsamps;
    double precision;

    po::options_description desc("Allowed options");
    // clang-format off
    desc.add_options()
        ("help", "help message")
        ("verbose", "enable some verbose")
        ("args", po::value<std::string>(&args)->default_value(""), "device address args [default = \"\"]")
        ("subdev", po::value<std::string>(&subdev), "Subdevice specification (default: first subdevice, often 'A')")
        ("tx_wave_freq", po::value<double>(&tx_wave_freq)->default_value(507.123e3), "Transmit wave frequency in Hz")
        ("tx_wave_ampl", po::value<double>(&tx_wave_ampl)->default_value(0.7), "Transmit wave amplitude")
        ("rx_offset", po::value<double>(&rx_offset)->default_value(.9344e6), "RX LO offset from the TX LO in Hz")
        ("freq_start", po::value<double>(&freq_start), "Frequency start in Hz (do not specify for default)")
        ("freq_stop", po::value<double>(&freq_stop), "Frequency stop in Hz (do not specify for default)")
        ("freq_step", po::value<double>(&freq_step)->default_value(default_freq_step), "Step size for LO sweep in Hz")
        ("nsamps", po::value<size_t>(&nsamps), "Samples per data capture")
        ("precision", po::value<double>(&precision)->default_value(default_precision), "Correction precision (default=0.0001)")
    ;
    // clang-format on

    po::variables_map vm;
    po::store(po::parse_command_line(argc, argv, desc), vm);
    po::notify(vm);

    // print the help message
    if (vm.count("help")) {
        std::cout << boost::format("USRP Generate TX IQ Balance Calibration Table %s")
                         % desc
                  << std::endl;
        std::cout << "This application measures leakage between RX and TX on a "
                     "transceiver daughterboard to self-calibrate.\n"
                     "Note: Not all daughterboards support this feature. Refer to the "
                     "UHD manual for details.\n"
                  << std::endl;
        return EXIT_FAILURE;
    }

    // Create a USRP device
    uhd::usrp::multi_usrp::sptr usrp = setup_usrp_for_cal(args, subdev, serial);

    if (not vm.count("nsamps"))
        nsamps = size_t(usrp->get_rx_rate() / default_fft_bin_size);

    // create a receive streamer
    uhd::stream_args_t stream_args("fc32"); // complex floats
    uhd::rx_streamer::sptr rx_stream = usrp->get_rx_stream(stream_args);

    // create a transmit streamer
    uhd::tx_streamer::sptr tx_stream = usrp->get_tx_stream(stream_args);

    // create a transmitter thread
    boost::thread_group threads;
    threads.create_thread(
        boost::bind(&tx_thread, usrp, tx_stream, tx_wave_freq, tx_wave_ampl));

    // re-usable buffer for samples
    std::vector<samp_type> buff;

    // store the results here
    std::vector<result_t> results;

    if (not vm.count("freq_start"))
        freq_start = usrp->get_fe_tx_freq_range().start();
    if (not vm.count("freq_stop"))
        freq_stop = usrp->get_fe_tx_freq_range().stop();

    // check start and stop frequencies
    if (freq_start < usrp->get_fe_tx_freq_range().start()) {
        std::cerr << "freq_start must be " << usrp->get_fe_tx_freq_range().start()
                  << " or greater for this daughter board" << std::endl;
        return EXIT_FAILURE;
    }
    if (freq_stop > usrp->get_fe_tx_freq_range().stop()) {
        std::cerr << "freq_stop must be " << usrp->get_fe_tx_freq_range().stop()
                  << " or less for this daughter board" << std::endl;
        return EXIT_FAILURE;
    }

    // check rx_offset
    double min_rx_offset =
        usrp->get_rx_freq_range().start() - usrp->get_fe_tx_freq_range().start();
    double max_rx_offset =
        usrp->get_rx_freq_range().stop() - usrp->get_fe_tx_freq_range().stop();
    if (rx_offset < min_rx_offset or rx_offset > max_rx_offset) {
        std::cerr << "rx_offset must be between " << min_rx_offset << " and "
                  << max_rx_offset << " for this daughter board" << std::endl;
        return EXIT_FAILURE;
    }

    std::cout << boost::format("Calibration frequency range: %d MHz -> %d MHz")
                     % (freq_start / 1e6) % (freq_stop / 1e6)
              << std::endl;

    size_t tx_error_count = 0;
    for (double tx_lo_i = freq_start; tx_lo_i <= freq_stop; tx_lo_i += freq_step) {
        const double tx_lo = tune_rx_and_tx(usrp, tx_lo_i, rx_offset);

        // frequency constants for this tune event
        const double actual_rx_rate = usrp->get_rx_rate();
        const double actual_tx_freq = usrp->get_tx_freq();
        const double actual_rx_freq = usrp->get_rx_freq();
        const double bb_tone_freq   = actual_tx_freq + tx_wave_freq - actual_rx_freq;
        const double bb_imag_freq   = actual_tx_freq - tx_wave_freq - actual_rx_freq;

        // reset TX IQ balance
        usrp->set_tx_iq_balance(0.0);

        // set optimal RX gain setting for this frequency
        set_optimal_rx_gain(usrp, rx_stream, tx_wave_freq);

        // capture initial uncorrected value
        capture_samples(usrp, rx_stream, buff, nsamps);
        const double initial_suppression =
            compute_tone_dbrms(buff, bb_tone_freq / actual_rx_rate)
            - compute_tone_dbrms(buff, bb_imag_freq / actual_rx_rate);

        // bounds and results from searching
        double phase_corr_start = -1.0;
        double phase_corr_stop  = 1.0;
        double phase_corr_step =
            (phase_corr_stop - phase_corr_start) / (num_search_steps + 1);
        double ampl_corr_start = -1.0;
        double ampl_corr_stop  = 1.0;
        double ampl_corr_step =
            (ampl_corr_stop - ampl_corr_start) / (num_search_steps + 1);
        double best_suppression = 0;
        double best_phase_corr  = 0;
        double best_ampl_corr   = 0;
        while (phase_corr_step >= precision or ampl_corr_step >= precision) {
            for (double phase_corr = phase_corr_start + phase_corr_step;
                 phase_corr <= phase_corr_stop - phase_corr_step;
                 phase_corr += phase_corr_step) {
                for (double ampl_corr = ampl_corr_start + ampl_corr_step;
                     ampl_corr <= ampl_corr_stop - ampl_corr_step;
                     ampl_corr += ampl_corr_step) {
                    const std::complex<double> correction(ampl_corr, phase_corr);
                    usrp->set_tx_iq_balance(correction);

                    // receive some samples
                    capture_samples(usrp, rx_stream, buff, nsamps);
                    // check for TX errors in the current captured iteration
                    if (has_tx_error(tx_stream)) {
                        std::cout << "[WARNING] TX error detected! "
                                  << "Repeating current iteration" << std::endl;
                        // Undo ampl corr step
                        ampl_corr -= ampl_corr_step;
                        tx_error_count++;
                        if (tx_error_count >= MAX_NUM_TX_ERRORS) {
                            throw uhd::runtime_error(
                                "Too many TX errors. Aborting calibration.");
                        }
                        continue;
                    }
                    const double tone_dbrms =
                        compute_tone_dbrms(buff, bb_tone_freq / actual_rx_rate);
                    const double imag_dbrms =
                        compute_tone_dbrms(buff, bb_imag_freq / actual_rx_rate);
                    const double suppression = tone_dbrms - imag_dbrms;

                    if (suppression > best_suppression) {
                        best_suppression = suppression;
                        best_phase_corr  = phase_corr;
                        best_ampl_corr   = ampl_corr;
                    }
                }
            }
            phase_corr_start = best_phase_corr - phase_corr_step;
            phase_corr_stop  = best_phase_corr + phase_corr_step;
            phase_corr_step =
                (phase_corr_stop - phase_corr_start) / (num_search_steps + 1);
            ampl_corr_start = best_ampl_corr - ampl_corr_step;
            ampl_corr_stop  = best_ampl_corr + ampl_corr_step;
            ampl_corr_step  = (ampl_corr_stop - ampl_corr_start) / (num_search_steps + 1);
        }
        if (best_suppression > initial_suppression) // keep result
        {
            result_t result;
            result.freq      = tx_lo;
            result.real_corr = best_ampl_corr;
            result.imag_corr = best_phase_corr;
            result.best      = best_suppression;
            result.delta     = best_suppression - initial_suppression;
            results.push_back(result);
            if (vm.count("verbose"))
                std::cout << boost::format(
                                 "TX IQ: %f MHz: best suppression %f dB, corrected %f dB")
                                 % (tx_lo / 1e6) % result.best % result.delta
                          << std::endl;
            else
                std::cout << "." << std::flush;
        }

        // Reset underrun counts, start a new counter for the next frequency
        tx_error_count = 0;
    }
    std::cout << std::endl;

    // stop the transmitter
    threads.interrupt_all();
    std::this_thread::sleep_for(
        std::chrono::milliseconds(500)); // wait for threads to finish
    threads.join_all();

    store_results(results, "TX", "tx", "iq", serial);

    return EXIT_SUCCESS;
}
