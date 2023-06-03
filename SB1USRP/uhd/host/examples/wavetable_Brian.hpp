//
// Copyright 2010-2012,2014 Ettus Research LLC
// Copyright 2018 Ettus Research, a National Instruments Company
//
// SPDX-License-Identifier: GPL-3.0-or-later
//

#include <cmath>
#include <complex>
#include <stdexcept>
#include <string>
#include <vector>
#include <iostream>
#include <fstream>

// static const size_t wave_table_len = 8192;
static const size_t wave_table_len = 500;

// using namespace std;

class wave_table_class_Brian
{
public:
    wave_table_class_Brian(const std::string& wave_type, const float ampl, std::string signal_file)
        : _wave_table_Brian(wave_table_len)
    {
        // compute real wave table with 1.0 amplitude
        std::vector<float> real_wave_table(wave_table_len);
        std::vector<float> imag_wave_table(wave_table_len);
        if (wave_type == "OFDM") {

            // file name
            std::string fileIn = signal_file;  

            // count row number
            std::ifstream rowCounter(fileIn);
            size_t rows = 0;
            std::string line; // trash
            if(rowCounter.is_open())
            {
                while(!rowCounter.eof())
                {
                    getline(rowCounter,line);
                    rows++;
                    //std::cout<<"hello"<<std::endl;
                }
                rowCounter.close();
            }

            std::ifstream reader(fileIn);
            rows--; // the last row is blank, so delete it. 

            // assign data type
            double real_wave_table_tmp;
            double imag_wave_table_tmp;

            // read in data
            if (reader.is_open()) {
                for (size_t i = 0; i < rows; i++) {
                    reader >> real_wave_table_tmp;
                    real_wave_table[i] = real_wave_table_tmp;

                    reader >> imag_wave_table_tmp;
                    imag_wave_table[i] = imag_wave_table_tmp;

                    _wave_table_Brian[i] = 
                        std::complex<float>(ampl * real_wave_table[i], ampl * imag_wave_table[i]);
                }
            }
            std::cout<<std::endl;
            std::cout<<"read file flag: "<<reader.is_open()<<std::endl;
                if (reader.is_open() == 1)
                    std::cout<<"wavetable generated! - Brian"<<std::endl;
                else
                    throw std::runtime_error("Signal file not found! ");


        } else if (wave_type == "SINE") {
            static const double tau = 2 * std::acos(-1.0);  // tau = 2pi
            for (size_t i = 0; i < wave_table_len; i++){
                real_wave_table[i] = std::cos((tau * i) / wave_table_len);
                imag_wave_table[i] = std::sin((tau * i) / wave_table_len);
            }

            for (size_t i = 0; i < wave_table_len; i++) {
                _wave_table_Brian[i] = std::complex<float>(ampl * real_wave_table[i], 
                ampl * imag_wave_table[i]);
            }
        } else
            throw std::runtime_error("unknown waveform type: " + wave_type);

        




        // // compute i and q pairs with 90% offset and scale to amplitude
        // for (size_t i = 0; i < wave_table_len; i++) {
        //     const size_t q = (i + (3 * wave_table_len) / 4) % wave_table_len;
        //     _wave_table[i] =
        //         std::complex<float>(ampl * real_wave_table[i], ampl * real_wave_table[q]);
        // }

        

    }

    inline std::complex<float> operator()(const size_t index) const
    {
        return _wave_table_Brian[index % wave_table_len];
    }

private:
    std::vector<std::complex<float>> _wave_table_Brian;
};
