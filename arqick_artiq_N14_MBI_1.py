import numpy as np
from artiq.experiment import *
from arqick_artiq_red_config import ARQICK_DoPulses_Red

class ARQICK_N14_MBI_1(EnvExperiment, ARQICK_DoPulses_Red):
    kernel_invariants = (ARQICK_DoPulses_Red.kernel_invariants | {
                        "tau_before_first_readout_mu",
                        "tau_after_first_readout",
                        "laser1_pulse_width_correction_mu",
                        "n14_spin_readout_mu",
                        "n14_spin_readout_correction_mu",
                        "temp_data_N14_check"
                        })
    
    def build(self):
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
        self.inital_delay_tdds = 10000
        self.tau_before_first_readout = self.after_red_op_to_mw_buffer + self.inital_delay_tdds*self.qick_tdds_ns*2 +  self.pi2_duration_tdds*self.qick_tdds_ns 
        self.tau_before_first_readout_mu = self.core.seconds_to_mu(self.tau_before_first_readout)
        self.tau_after_first_readout = [] 
        self.n14_spin_readout_tdds = 5000 # 400ns
        self.n14_spin_readout = self.n14_spin_readout_tdds*self.qick_tdds_ns
        self.n14_spin_readout_mu = self.core.seconds_to_mu(self.n14_spin_readout)
        self.n14_spin_readout_correction = self.n14_spin_readout + self.laser1_pulse_width_correction
        self.n14_spin_readout_correction_mu = self.core.seconds_to_mu(self.n14_spin_readout_correction)
        self.set_dataset("N14_check", [], broadcast=False)
    
    def run(self):
        self.initialize()
        self.tau_list = np.linspace(self.freq_low, self.freq_high, self.freq_step)
        self.tau_list2 = np.linspace(self.freq_low, self.freq_high, self.freq_step)
        self.tau_after_first_readout = self.tau_list2*0 + self.after_red_op_to_mw_buffer + self.sweep_pi_tdds/2*self.qick_tdds_ns + self.after_mw_to_spin_readout_buffer - self.laser1_pulse_width_correction
        self.tau_list2 = self.tau_before_first_readout + self.tau_after_first_readout + self.n14_spin_readout + self.laser1_pulse_width_correction
        self.tau_after_first_readout = [self.core.seconds_to_mu(t) for t in self.tau_after_first_readout]

        # self.data_size = len(self.tau_list[:-1])
        # self.tau_list2 = self.tau_list2[:-1]
        # self.tau_after_first_readout = self.tau_after_first_readout[:-1]
        
        # self.sweep_config = self.config_qick(self.default_config)
        self.set_dataset("tau", self.tau_list)
        print(self.tau_list)
        # total_time = self.experiment_time_calculator()
        # self.set_dataset("block_n_cycles", self.block_n_cycles)    
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
        # self.pulse_qick(self.sweep_config)
        # print(f"starting block {i+1}/{len(self.block_n_cycles)} with {self.block_n_cycles[i]} cycles")
        self.do_pulses_specific(freq=self.freq_resonant)
        print("on experiment done")
            # # calibration pulses with rabi
            # self.temp_data_sr = [0] * 2
            # self.temp_data_cr = [0] * 2
            # self.temp_data_N14_check = [0] * 2
            # self.data_size = 2
            # self.n_cycles = self.n_cycles_calibration
            # self.tau_list2 = self.tau_calibration
            # self.pulse_qick_calibration(self.calibration_config)
            # self.do_pulses(freq=self.freq_off_resonant)

        # print('experiment done')

    @kernel
    def do_pulses_specific(self, freq):
        self.core.reset()
        for i in range(self.n_cycles):
            self.pulse_artiq_specific(0, True)   
            for j in range(self.data_size-1):
                with parallel:
                    self.pulse_artiq_specific(j+1, False)
                    self.temp_data_N14_check[j] = self.ttl0_counter.fetch_count()
                    self.temp_data_sr[j] = self.ttl0_counter.fetch_count()
                    self.temp_data_cr[j] = self.ttl0_counter.fetch_count()
            self.temp_data_N14_check[self.data_size-1] = self.ttl0_counter.fetch_count()
            self.temp_data_sr[self.data_size-1] = self.ttl0_counter.fetch_count()
            self.temp_data_cr[self.data_size-1] = self.ttl0_counter.fetch_count()
            # calls an rpc to append to dataset from kernel
            if freq == self.freq_resonant:
                self.append_to_dataset("N14_check", self.temp_data_N14_check)
                self.append_to_dataset("on", self.temp_data_sr)
                self.append_to_dataset("on_cr", self.temp_data_cr)
            else:
                self.append_to_dataset("off", self.temp_data_sr)
                self.append_to_dataset("off_cr", self.temp_data_cr)
            self.core.break_realtime()  # although 125ms between cycles, to prevent underflow, good to let qick and artiq relax
        self.core.wait_until_mu(now_mu())

    @kernel
    def pulse_artiq_specific(self, index, start: bool):
        if start: 
            with parallel:
                self.ttl6.pulse_mu(self.pulse_width_mu)
                with sequential:
                    delay_mu(self.inherent_artiq_ttl2_to_ttl6_delay_mu) # needed to be in line with pulse with parallel since ttl6 pulse takes longer to come out
                    close_mu = self.ttl2.gate_rising_mu(self.ttl2_window_mu) 
        else:
            close_mu = self.ttl2.gate_rising_mu(self.ttl2_window_mu)
        trigger_mu = self.ttl2.timestamp_mu(close_mu)
        if trigger_mu >= 0:
            at_mu(trigger_mu) 
            delay_mu(self.after_artiq_recieve_trigger_delay_mu) # could combine green to red 2 delay here

            # Green -> A1 -> MW(dur) -> Ex+C -> CR+C
            cursor = now_mu()                           # red 1 sequence
            delay_mu(self.green_init_duration_mu)
            delay_mu(self.a1_optical_pump_mu)
            delay_mu(self.tau_before_first_readout_mu)
            self.urukul0_ch0.sw.on()
            delay_mu(self.n14_spin_readout_correction_mu)
            self.urukul0_ch0.sw.off()
            delay_mu(self.tau_after_first_readout[index])             # MW (includes only includes mw buffers)
            self.urukul0_ch0.sw.on()
            delay_mu(self.ex_spin_readout_correction_mu)
            self.urukul0_ch0.sw.off()
            delay_mu(self.wait_time_laser1_mu)                 # wait time between spin and charge readout
            self.urukul0_ch0.sw.on()
            delay_mu(self.charge_readout_laser1_mu)
            self.urukul0_ch0.sw.off()

            at_mu(cursor)                               # red 2 sequence
            delay_mu(self.red2_to_red1_mu)
            delay_mu(self.green_init_duration_mu) 
            self.urukul0_ch3.sw.on()
            delay_mu(self.a1_optical_pump_correction_mu)
            self.urukul0_ch3.sw.off()
            delay_mu(self.tau_list2[index]) 
            delay_mu(self.ex_spin_readout_mu)
            delay_mu(self.wait_time_laser2_mu)
            self.urukul0_ch3.sw.on()
            delay_mu(self.charge_readout_laser2_mu)
            self.urukul0_ch3.sw.off()

            at_mu(cursor)                               # green+readout sequence
            delay_mu(self.green_to_red1_mu)
            self.ttl4.pulse_mu(self.green_init_duration_mu)
            delay_mu(self.a1_optical_pump_mu)
            delay_mu(self.read_to_green_mu) 
            delay_mu(self.tau_before_first_readout_mu)
            self.ttl0_counter.gate_rising_mu(self.n14_spin_readout_mu)
            delay_mu(self.tau_after_first_readout[index])   
            delay_mu(self.laser1_pulse_width_correction_mu)         
            self.ttl0_counter.gate_rising_mu(self.ex_spin_readout_mu)
            delay_mu(self.wait_time_mu)
            self.ttl0_counter.gate_rising_mu(self.charge_readout_mu)

            delay_mu(self.artiq_experiment_padding_mu)  # padding to prevent underflow
        else:
            print("No rfsoc trigger detected at index ", index)
            self.core.break_realtime()


    # @rpc
    # def config_qick(self, default_config):
    #     config = copy(default_config)
    #     config.mw_gain = self.mw_gain
    #     config.freq_fMHz = self.freq_resonant
    #     config.mw_pi2_tdds = self.pi2_duration_tdds
    #     config.mBI_pi_tdds = self.mBI_pi_duration_tdds
    #     config.mBI_freq_fMHz = self.mBI_freq
    #     config.mBI_mw_gain = self.mBI_mw_gain
    #     config.sweep_pi_tdds = self.sweep_pi_tdds
    #     config.sweep_mw_gain = self.sweep_mw_gain
    #     config.inital_delay_tdds = self.inital_delay_tdds
    #     config.N14_measurement_delay_tdds = round((self.n14_spin_readout + self.after_red_op_to_mw_buffer + self.inital_delay_tdds*self.qick_tdds_ns)/self.qick_tdds_ns)
    #     # remember the sweep is inclusive of the start and end values
    #     config.add_linear_sweep(name = "freq", unit = "fMHz", start = self.freq_low, stop = self.freq_high, delta=self.freq_step)

    #     # if we dont want to change the config file, then this tau_list will be used as the n_cpmg_list
    #     self.tau_list = np.linspace(config.freq_start_fMHz, config.freq_end_fMHz, config.nsweep_points)
    #     self.tau_list2 = np.linspace(config.freq_start_fMHz, config.freq_end_fMHz, config.nsweep_points)
    #     self.tau_after_first_readout = self.tau_list2*0 + self.after_red_op_to_mw_buffer + self.sweep_pi_tdds/2*self.qick_tdds_ns + self.after_mw_to_spin_readout_buffer - self.laser1_pulse_width_correction
    #     self.tau_list2 = self.tau_before_first_readout + self.tau_after_first_readout + self.n14_spin_readout + self.laser1_pulse_width_correction
    #     self.tau_after_first_readout = [self.core.seconds_to_mu(t) for t in self.tau_after_first_readout]
        
    #     config.pulse_seq_delay_tus = round(self.after_mw_to_spin_readout_buffer*1e6 + self.read_to_green*1e6 + self.ex_spin_readout*1e6 + self.wait_time*1e6 + self.charge_readout*1e6 + self.qick_experiment_padding*1e6,5) # after delay | the delay after qick pulses
    #     config.reps=1
    #     config.pmod_out_pin = 0 
    #     config.pmod_out_pulse_width_tns = 300
    #     config.inherent_trigger_to_pulses_delay_tns = self.inherent_qick_delay_ns*1e9
    #     config.pmod_out_trig_delay_tus = round((self.t_buffer_us*1e6 + self.green_to_red1*1e6 + self.green_init_duration*1e6 + self.a1_optical_pump*1e6 + self.after_red_op_to_mw_buffer*1e6 - config.inherent_trigger_to_pulses_delay_tns/1000),5) # before delay |the delay before qick pulses | to account for inherent delay for mw pulse to come out
    #     return config
    
    # @rpc
    # def pulse_qick(self, config):
    #     soc = qd.soc
    #     prog = N14MBI(config)
    #     prog.run_rounds(soc, rounds=0, start_src="external")