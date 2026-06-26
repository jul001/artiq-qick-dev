from artiq.experiment import *
import numpy as np
from arqick_artiq_red_cpmg_mbp_config import ARQICK_DoPulses_Red_CPMG_Mbp

class ARQICK_red_N14MBP_200ps(EnvExperiment, ARQICK_DoPulses_Red_CPMG_Mbp):
    kernel_invariants = (ARQICK_DoPulses_Red_CPMG_Mbp.kernel_invariants | {
                        "tau_before_first_readout_mu",
                        "tau_after_first_readout",
                        "laser1_pulse_width_correction_mu",
                        "n14_spin_readout_mu",
                        "n14_spin_readout_correction_mu",
                        "temp_data_N14_check",
                        "delay_after_prep_nv_n14_mu",
                        "delay_after_pulse_artiq_n14_mu",
                        "ttl2_to_qick_readout_mu",
                        "tot_time_after_pmod_out_to_qick_readout_mu",
                        })
    
    def build(self):
        # to mimick photons
        self.setattr_argument("ttl4_pulse_width", NumberValue(100*ns, min=0, step=10, unit="ns", precision=2))
        self.setattr_argument("ttl4_pulse_delay", NumberValue(50*ns, min=0, step=10, unit="ns", precision=2))
        
        self.setattr_argument("pi2_duration_tdds", NumberValue(200, precision=0, step=1))
        self.setattr_argument("mBI_pi_duration_tdds", NumberValue(7314, precision=0, step=1))
        self.setattr_argument('mBI_mw_gain', NumberValue(8000, precision=0, min=0, max=31000, step=1))
        self.setattr_argument("mBI_freq", NumberValue(410, precision=4, step=1))
        self.setattr_argument("freq_low", NumberValue(407, precision=4, step=1))
        self.setattr_argument("freq_high", NumberValue(411, precision=4, step=1))
        self.setattr_argument("freq_step", NumberValue(5, precision=0, step=1))
        self.setattr_argument("sweep_pi_tdds", NumberValue(7314 , precision=0, step=1))
        self.setattr_argument('sweep_mw_gain', NumberValue(8000, precision=0, min=0, max=31000, step=1))
        self.build_config()
        
    def prepare(self):
        self.prepare_config(Fineres=True)
        self.inital_delay_tdds = 10000     # =2.034us
        self.tau_before_first_readout = (self.after_red_op_to_mw_buffer + self.inital_delay_tdds*self.qick_tdds_ns*2 + self.pi2_duration_tdds*self.qick_tdds_ns)
        print("self.tau_before_first_readout:",self.tau_before_first_readout)
        self.tau_before_first_readout_mu = self.core.seconds_to_mu(self.tau_before_first_readout)
        self.tau_after_first_readout = [] 
        self.n14_spin_readout_tdds = 5000  # =1us
        self.n14_spin_readout = self.n14_spin_readout_tdds*self.qick_tdds_ns
        self.n14_spin_readout_mu = self.core.seconds_to_mu(self.n14_spin_readout)
        self.n14_spin_readout_correction = self.n14_spin_readout + self.laser1_pulse_width_correction
        self.n14_spin_readout_correction_mu = self.core.seconds_to_mu(self.n14_spin_readout_correction)
        
        self.ttl4_pulse_width_mu = self.core.seconds_to_mu(self.ttl4_pulse_width)
        self.ttl4_pulse_delay_mu = self.core.seconds_to_mu(self.ttl4_pulse_delay)

        # overwrite what is in the other config file
        self.ttl2_window_ns = 1000 * ns  # window to catch the trigger from rfsoc. adding 1us leeway
        self.ttl2_window_mu = self.core.seconds_to_mu(self.ttl2_window_ns)

        self.inherent_artiq_ttl2_to_ttl5_delay_ns = 1 * ns  # 140 ns works
        self.inherent_artiq_ttl2_to_ttl5_delay_mu = self.core.seconds_to_mu(self.inherent_artiq_ttl2_to_ttl5_delay_ns)

        self.qick_processing_time_after_readout_us = 5 * us
        self.qick_readout_integration_time_us = 1 * us
        self.ttl2_leeway_ns = 500 * ns
        self.ttl2_leeway_mu = self.core.seconds_to_mu(self.ttl2_leeway_ns)
        self.ttl5_to_qick_pmod_out_delay_us = self.qick_processing_time_after_readout_us - self.ttl5_pulse_width_ns - self.ttl2_leeway_ns
        self.ttl5_to_qick_pmod_out_delay_mu = self.core.seconds_to_mu(self.ttl5_to_qick_pmod_out_delay_us)

        self.inherent_artiq_ttl2_to_ttl6_delay_ns = self.inherent_artiq_ttl6_delay_ns - self.inherent_artiq_ttl2_gate_rising_delay_ns
        self.inherent_artiq_ttl2_to_ttl6_delay_mu = self.core.seconds_to_mu(self.inherent_artiq_ttl2_to_ttl6_delay_ns)
        # self.inherent_artiq_qick_trigger_delay_ns_ = 377 * ns
        self.inherent_artiq_qick_trigger_delay_ns = 700 * ns
        self.ttl2_window_start_ns = self.inherent_artiq_qick_trigger_delay_ns + self.inherent_qick_delay_ns + 1000*ns # window to catch the trigger from rfsoc. adding 1us leeway
        self.ttl2_window_start_mu = self.core.seconds_to_mu(self.ttl2_window_start_ns)

        self.delay_after_prep_nv_n14 = 12 * us
        self.delay_after_prep_nv_n14_mu = self.core.seconds_to_mu(self.delay_after_prep_nv_n14)
        self.delay_after_ttl5_pulse_nv_n14_us = 10 * us
        self.delay_after_ttl5_pulse_nv_n14_mu = self.core.seconds_to_mu(self.delay_after_ttl5_pulse_nv_n14_us)
        self.delay_after_pulse_artiq_n14 = 5 * us
        # self.delay_after_pulse_artiq_n14_mu = self.core.seconds_to_mu(self.delay_after_pulse_artiq_n14 
        #                                                               + self.after_artiq_recieve_trigger_delay_ns)
        self.delay_after_pulse_artiq_n14_mu = self.core.seconds_to_mu(self.after_artiq_recieve_trigger_delay_ns)
        
        self.duration_after_first_readout = (self.after_red_op_to_mw_buffer + self.sweep_pi_tdds/2*self.qick_tdds_ns 
                                        + self.after_mw_to_spin_readout_buffer - self.laser1_pulse_width_correction)
        self.duration_after_first_readout_mu = self.core.seconds_to_mu(self.duration_after_first_readout)

        self.prep_nv_n14_total_duration_us = (self.read_to_red1 + self.green_init_duration + self.a1_optical_pump 
                                          + self.tau_before_first_readout + self.n14_spin_readout 
                                          + self.duration_after_first_readout + self.delay_after_prep_nv_n14)
        self.prep_nv_n14_total_duration_mu = self.core.seconds_to_mu(self.prep_nv_n14_total_duration_us)

        self.ttl2_to_qick_readout = (self.prep_nv_n14_total_duration_us - self.delay_to_align_second_ttl5_to_readout_window_ns)
        self.ttl2_to_qick_readout_mu = self.core.seconds_to_mu(self.ttl2_to_qick_readout) ################

        self.tot_time_after_pmod_out_to_qick_readout = (self.prep_nv_n14_total_duration_us
                                                   - self.delay_to_align_second_ttl5_to_readout_window_ns)
        self.tot_time_after_pmod_out_to_qick_readout_mu = self.core.seconds_to_mu(self.tot_time_after_pmod_out_to_qick_readout)

        self.delay_to_align_qick_readout_to_ttl5 = 0.068 * us
        
        #

        self.set_dataset("N14_check", [], broadcast=False)
    
    def run(self):
        self.initialize()

        self.random_counts = np.random.randint(low=1, high=5, size=10000)
        self.counts_data = [0] * len(self.random_counts)

        self.tau_list = np.linspace(self.freq_low, self.freq_high, self.freq_step)
        self.tau_list2 = np.linspace(self.freq_low, self.freq_high, self.freq_step)
        # self.tau_after_first_readout = self.tau_list2*0 + self.after_red_op_to_mw_buffer + self.sweep_pi_tdds/2*self.qick_tdds_ns + self.after_mw_to_spin_readout_buffer - self.laser1_pulse_width_correction
        self.tau_after_first_readout = self.tau_list2*0 + self.after_mw_to_spin_readout_buffer - self.laser1_pulse_width_correction
        self.tau_list2 = self.tau_before_first_readout + self.tau_after_first_readout + self.n14_spin_readout + self.laser1_pulse_width_correction
        self.tau_after_first_readout = [self.core.seconds_to_mu(t) for t in self.tau_after_first_readout]
        # self.data_size = len(self.tau_list[:-1])
        # self.tau_list2 = self.tau_list2[:-1]
        # self.tau_after_first_readout = self.tau_after_first_readout[:-1]
        
        # self.sweep_config = self.config_qick(self.default_config)
        self.set_dataset("tau", self.tau_list)
        print(self.tau_list)
        # total_time, self.block_n_cycles = self.experiment_time_calculator()
        # self.set_dataset("block_n_cycles", 1)    # self.set_dataset("block_n_cycles", self.block_n_cycles)
        # print(f"expected experiment time: {total_time} minutes")
        self.tau_list2 = [self.core.seconds_to_mu(t) for t in self.tau_list2]
        self.temp_tau_list = self.tau_list2
        
        # self.calibration_config, self.tau_calibration = self.config_calibration(self.default_config)
        # self.tau_calibration = [self.core.seconds_to_mu(t) for t in self.tau_calibration]

        # for i in range(len(self.block_n_cycles)):
            # self.n_cycles = self.block_n_cycles[i]
        self.tau_list2 = self.temp_tau_list 
        self.data_size = len(self.tau_list2)
        self.temp_data_sr = [0] * self.data_size        # for spin readout
        self.temp_data_cr = [0] * self.data_size        # for charge readout
        self.temp_data_N14_check = [0] * self.data_size     # for N14 check readout
        self.temp_data_repeats = [0] * self.data_size  # for tracking repeats per cycle
        # self.pulse_qick(self.sweep_config)
        # print(f"starting block {i+1}/{len(self.block_n_cycles)} with {self.block_n_cycles[i]} cycles")
        self.do_pulses_specific(freq=self.freq_resonant)
        
            # calibration pulses with rabi
            # self.temp_data_sr = [0] * 2
            # self.temp_data_cr = [0] * 2
            # self.temp_data_N14_check = [0] * 2
            # self.data_size = 2
            # self.n_cycles = self.n_cycles_calibration
            # self.tau_list2 = self.tau_calibration
            # self.pulse_qick_calibration(self.calibration_config)
            # self.do_pulses(freq=self.freq_off_resonant)

        print('experiment done')

    @kernel
    def do_pulses_specific(self, freq):
        self.core.reset()
        random_counts_index = 0
        for i in range(self.n_cycles):
            n14_counts = 0
            n_repeats = 0
            while n14_counts < self.photon_threshold: # n14_counts < self.photon_threshold:
                loop_cursor = now_mu()
                self.prep_nv_n14(start=True, n_rep=n_repeats, crsr=loop_cursor, random_counts_index=random_counts_index)
                with parallel:
                    delay_mu(self.delay_after_prep_nv_n14_mu) # 12 us
                    n_repeats += 1
                    random_counts_index += 1
                    n14_counts = self.ttl0_counter.fetch_count()
            self.pulse_artiq_specific(0)   
            for j in range(self.data_size-1):
                start = now_mu()

                self.temp_data_repeats[j] = n_repeats
                self.temp_data_N14_check[j] = n14_counts
                self.temp_data_sr[j] = self.ttl0_counter.fetch_count()
                self.temp_data_cr[j] = self.ttl0_counter.fetch_count()
                n14_counts = 0
                n_repeats = 0
                
                at_mu(start + self.delay_after_pulse_artiq_n14_mu) # 5 us
                while n14_counts < self.photon_threshold:
                    loop_cursor = now_mu()
                    self.prep_nv_n14(start=False, n_rep=n_repeats, crsr=loop_cursor, random_counts_index=random_counts_index)
                    with parallel:
                        delay_mu(self.delay_after_prep_nv_n14_mu)
                        n_repeats += 1
                        random_counts_index += 1
                        n14_counts = self.ttl0_counter.fetch_count()
                self.pulse_artiq_specific(j+1)
            self.temp_data_N14_check[self.data_size-1] = n14_counts
            self.temp_data_repeats[self.data_size - 1] = n_repeats
            self.temp_data_sr[self.data_size-1] = self.ttl0_counter.fetch_count()
            self.temp_data_cr[self.data_size-1] = self.ttl0_counter.fetch_count()
            # calls an rpc to append to dataset from kernel
            if freq == self.freq_resonant:
                self.append_to_dataset("N14_check", self.temp_data_N14_check)
                self.append_to_dataset("on", self.temp_data_sr)
                self.append_to_dataset("on_cr", self.temp_data_cr)
                self.append_to_dataset("on_repeats_per_cycle", self.temp_data_repeats)
            else:
                self.append_to_dataset("off", self.temp_data_sr)
                self.append_to_dataset("off_cr", self.temp_data_cr)
                self.append_to_dataset("off_repeats_per_cycle", self.temp_data_repeats)
            self.core.break_realtime()  # although 125ms between cycles, to prevent underflow, good to let qick and artiq relax
        self.core.wait_until_mu(now_mu())

    @kernel
    def prep_nv_n14(self, start, n_rep, crsr, random_counts_index):
        if start and n_rep == 0: 
            with parallel:
                self.ttl6.pulse_mu(self.pulse_width_mu)
                with sequential:
                    delay_mu(self.inherent_artiq_ttl2_to_ttl6_delay_mu) # needed to be in line with pulse with parallel since ttl6 pulse takes longer to come out
                    close_mu = self.ttl2.gate_rising_mu(self.ttl2_window_start_mu) 
        # else:
        #     close_mu = self.ttl2.gate_rising_mu(self.ttl2_window_start_mu)
            trigger_mu = self.ttl2.timestamp_mu(close_mu)
            if trigger_mu >= 0:
                at_mu(trigger_mu) 
                delay_mu(self.after_artiq_recieve_trigger_delay_mu) # could combine green to red 2 delay here

                cursor = now_mu()                   # red 1 sequence
                at_mu(cursor)
                delay_mu(self.green_init_duration_mu)
                delay_mu(self.a1_optical_pump_mu)
                delay_mu(self.tau_before_first_readout_mu)
                self.urukul0_ch0.sw.on()
                delay_mu(self.n14_spin_readout_correction_mu)
                self.urukul0_ch0.sw.off()

                at_mu(cursor)                       # red 2 sequence
                delay_mu(self.red2_to_red1_mu)
                delay_mu(self.green_init_duration_mu)
                self.urukul0_ch3.sw.on()
                delay_mu(self.a1_optical_pump_correction_mu)
                self.urukul0_ch3.sw.off()
                delay_mu(self.tau_before_first_readout_mu)
                delay_mu(self.n14_spin_readout_correction_mu)

                at_mu(cursor)                       # green sequence
                delay_mu(self.green_to_red1_mu)
                self.ttl4.pulse_mu(self.green_init_duration_mu)
                delay_mu(self.a1_optical_pump_mu)
                delay_mu(self.tau_before_first_readout_mu)
                for k in range(self.random_counts[random_counts_index]):                      # qick program finished, start photon counting
                    self.ttl4.pulse_mu(self.ttl4_pulse_width_mu)
                    delay_mu(self.ttl4_pulse_delay_mu)

                at_mu(cursor)
                delay_mu(self.read_to_red1_mu)     # readout sequence
                delay_mu(self.green_init_duration_mu)
                delay_mu(self.a1_optical_pump_mu)
                delay_mu(self.tau_before_first_readout_mu)
                self.ttl0_counter.gate_rising_mu(self.n14_spin_readout_mu)
            else:
                print("No rfsoc trigger detected at index ")
                self.core.break_realtime()
        else:   
            at_mu(crsr)                       # red 1 sequence
            delay_mu(self.green_init_duration_mu)
            delay_mu(self.a1_optical_pump_mu)
            delay_mu(self.tau_before_first_readout_mu)
            self.urukul0_ch0.sw.on()
            delay_mu(self.n14_spin_readout_correction_mu)
            self.urukul0_ch0.sw.off()

            at_mu(crsr)                       # red 2 sequence
            delay_mu(self.red2_to_red1_mu)
            delay_mu(self.green_init_duration_mu)
            self.urukul0_ch3.sw.on()
            delay_mu(self.a1_optical_pump_correction_mu)
            self.urukul0_ch3.sw.off()
            delay_mu(self.tau_before_first_readout_mu)
            delay_mu(self.n14_spin_readout_correction_mu)

            at_mu(crsr)                       # green sequence
            delay_mu(self.green_to_red1_mu)
            self.ttl4.pulse_mu(self.green_init_duration_mu)
            delay_mu(self.a1_optical_pump_mu)
            delay_mu(self.tau_before_first_readout_mu)
            for k in range(self.random_counts[random_counts_index]):                      # qick program finished, start photon counting
                self.ttl4.pulse_mu(self.ttl4_pulse_width_mu)
                delay_mu(self.ttl4_pulse_delay_mu)

            at_mu(crsr)
            delay_mu(self.read_to_red1_mu)     # readout sequence
            delay_mu(self.green_init_duration_mu)
            delay_mu(self.a1_optical_pump_mu)
            delay_mu(self.tau_before_first_readout_mu)
            self.ttl0_counter.gate_rising_mu(self.n14_spin_readout_mu)

    @kernel
    def pulse_artiq_specific(self, index):
        cursor = now_mu()
        at_mu(cursor)
        self.ttl5.pulse_mu(self.ttl5_pulse_width_mu)                # 500 ns charge check passed -> send pulse to qick adc
        at_mu(cursor)
        delay_mu(self.inherent_artiq_ttl2_to_ttl5_delay_mu)         # 1 ns
        delay_mu(self.ttl5_to_qick_pmod_out_delay_mu)               # qick_processing time - ttl5_pulse_width = 5us - 500ns = 4.5us
        close_mu = self.ttl2.gate_rising_mu(self.ttl2_window_mu)    # 500 ns
        trigger_mu = self.ttl2.timestamp_mu(close_mu)
        
        if trigger_mu >= 0:
            at_mu(trigger_mu) 
            delay_mu(self.delay_after_ttl5_pulse_nv_n14_mu)        # 10 us
            delay_mu(self.tau_after_first_readout[index])   # includes the 3rd MW pulse (2us + 500tdds + 100ns) = 2.2us

            # MW(3rd) -> Ex+C -> CR+C
            cursor = now_mu()                               # red 1 sequence
            # delay_mu(self.tau_after_first_readout[index])   # includes the 3rd MW pulse
            self.urukul0_ch0.sw.on()
            delay_mu(self.ex_spin_readout_correction_mu)
            self.urukul0_ch0.sw.off()
            delay_mu(self.wait_time_laser1_mu)              # wait time between spin and charge readout
            self.urukul0_ch0.sw.on()
            delay_mu(self.charge_readout_laser1_mu)
            self.urukul0_ch0.sw.off()

            at_mu(cursor)                                   # red 2 sequence
            delay_mu(self.red2_to_red1_mu)
            # delay_mu(self.tau_after_first_readout[index])
            delay_mu(self.ex_spin_readout_mu)
            delay_mu(self.wait_time_laser2_mu)
            self.urukul0_ch3.sw.on()
            delay_mu(self.charge_readout_laser2_mu)
            self.urukul0_ch3.sw.off()

            at_mu(cursor)                                   # readout sequence
            delay_mu(self.read_to_red1_mu)
            # delay_mu(self.tau_after_first_readout[index])
            delay_mu(self.laser1_pulse_width_correction_mu)         
            self.ttl0_counter.gate_rising_mu(self.ex_spin_readout_mu)
            delay_mu(self.wait_time_mu)
            self.ttl0_counter.gate_rising_mu(self.charge_readout_mu)

            # delay_mu(self.artiq_experiment_padding_mu)  # padding to prevent underflow
        else:
            print("No rfsoc trigger detected at index ", index)
            self.core.break_realtime()