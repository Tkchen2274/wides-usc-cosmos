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

//static const size_t wave_table_len = 2500; // will have to assume this value can be varied
static const size_t wave_table_len = 500; // will have to assume this value can be varied
//static const size_t wave_table_len = 250; // will have to assume this value can be varied
//static const size_t wave_table_len = 50000; // will have to assume this value can be varied
//static const size_t wave_table_len = 25000; // will have to assume this value can be varied

using namespace std;

class wave_table_class
{
public:  
	wave_table_class(const std::string& wave_type, const float ampl)
		: _wave_table(wave_table_len)
	{

//               string fileIn = "Drone_signal_50MS_50MHz_20KHz.txt"; // I changed it from dsig7.txt to dsig8.txt
//		string fileIn = "MIMO_Drone_50MS_50MHz_SIMO_5usspace.txt"; // I changed it from dsig7.txt to dsig8.txt
//               string fileIn = "MIMO_Drone_signal_100MS_100MHz_SIMO_signal500us.txt";
//               string fileIn = "MIMO_Drone_100MS_100MHz_SIMO_500usv2space.txt";  
//		string fileIn = "MIMO_Drone_50MS_50MHz_SIMO_500usspacev2.txt";
		string fileIn = "MIMO_Drone_100MS_100MHz_SISO_5us.txt";  

                // open text file for OFDM waveform  03/02/20 dsig6 is the best
                //ifstream reader("dsig.txt");              // 50mss46mhz_20us_1000
                //ifstream reader("dsig1.txt");             // 40Mss38mhz_50us_8192 //step size.3
                //ifstream reader("dsig2.txt");             // 50Mss46mhz_50us_8192
                //ifstream reader("dsig3.txt");             // 50Mss46mhz_50us_2500
                //ifstream reader("dsig4.txt");             // 50Mss46mhz_50u_2500 less amplitude
                //ifstream reader("dsig5.txt");               // 50Mss46mhz_50us_2000 02/26
				//ifstream reader("dsig6.txt");             // 50Mss46mhz_50us_46_8192  //step size .4
                //ifstream reader("dsig7.txt");             // 50Mss46mhz_50us_46_2500
			    //ifstream reader("dsig8.txt");             // 50Mss46mhz_10us_46_500x5rep

                // counts the number of the rows in the txt file
                ifstream rowCounter(fileIn);
                int rows = 0;
                string line; // trash
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

                ifstream reader(fileIn);
                rows--; // the number of rows after counting is +1 s subtract 1 - one blank row at the end
                int rand = 0;
                //std::cin>>rand;

                double inI;
                double inQ;
                //int rows = 1000;
		int columns = 2;

		// compute real wave table with 1.0 amplitude
		std::vector<float> real_wave_table(wave_table_len);
		if (wave_type == "CONST") {
			for (size_t i = 0; i < wave_table_len; i++)
				real_wave_table[i] = 1.0;
		}
		else if (wave_type == "SQUARE") {
			for (size_t i = 0; i < wave_table_len; i++)
				real_wave_table[i] = (i < wave_table_len / 2) ? 0.0 : 1.0;
		}
		else if (wave_type == "RAMP") {
			for (size_t i = 0; i < wave_table_len; i++)
				real_wave_table[i] = 2.0 * i / (wave_table_len - 1) - 1.0;
		}
		else if (wave_type == "SINE") {
			static const double tau = 2 * std::acos(-1.0);
			for (size_t i = 0; i < wave_table_len; i++)
				real_wave_table[i] = std::sin((tau * i) / wave_table_len);
		}
		else if (wave_type == "OFDM")
		{
                    if(reader.is_open())
                    {
			for (size_t ii = 0; ii < rows; ii++)
			{
				reader >> inI;
                                //std::cout << inI <<endl;

				
				//real_wave_table[ii] = inI;
				for (size_t qq = 1; qq < columns; qq++)
				{

					real_wave_table[ii] = inI;
					reader >> inQ;
					real_wave_table[qq] = inQ;


					_wave_table[ii] =
						std::complex<float>(ampl * real_wave_table[ii], ampl * real_wave_table[qq]);
                                        //std::cout<< _wave_table[ii] << endl;


                                }

                        }
                    }
                    else
                        std::cout <<" UNABLE TO OPEN FILE" <<endl;



		}



		else
			throw std::runtime_error("unknown waveform type: " + wave_type);

		// compute i and q pairs with 90% offset and scale to amplitude if not OFDM
		if (wave_type != "OFDM")
		{
			for (size_t i = 0; i < wave_table_len; i++) 
			{

				const size_t q = (i + (3 * wave_table_len) / 4) % wave_table_len;
				_wave_table[i] =
					std::complex<float>(ampl * real_wave_table[i], ampl * real_wave_table[q]);
                                 std::cout<< _wave_table[i] << endl;

			}
		}
	}

	inline std::complex<float> operator()(const size_t index) const
	{
		return _wave_table[index % wave_table_len];
	}

private:
	std::vector<std::complex<float>> _wave_table;
        int rows;
};
