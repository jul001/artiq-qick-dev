from artiq.experiment import *
import numpy as np

class ARQICK_DoPulses_Red:
    kernel_invariants = {"data_size", 
                        "inherent_artiq_ttl2_to_ttl6_delay_mu", 
                        "ttl2_window_mu", 
                        "after_artiq_recieve_trigger_delay_mu",
                        "tau_list2",
                        "tau_calibration",
                        "n_cycles_calibration",
                        "read_to_green_mu",
                        "green_to_red1_mu",
                        "red2_to_red1_mu",
                        "artiq_experiment_padding_mu",
                        "temp_data_sr",
                        "temp_data_cr",
                        "pulse_width_mu",
                        "green_init_duration_mu",
                        "a1_optical_pump_mu",
                        "a1_optical_pump_correction_mu",
                        "ex_spin_readout_mu",
                        "ex_spin_readout_correction_mu",
                        "charge_readout_mu",
                        "charge_readout_laser1_mu",
                        "charge_readout_laser2_mu",
                        "wait_time_mu",
                        "wait_time_laser1_mu",
                        "wait_time_laser2_mu",
                        "dds_amp",
                        "U3_dds_amp"
                        }
    
    def build_config(self):
        self.setattr_device("core")
        self.setattr_device("ttl0_counter")
        self.setattr_device("ttl6")     # output to rfsoc
        self.setattr_device("ttl2")     # input trigger to artiq
        self.setattr_device("ttl4")     # green laser
        self.setattr_device("urukul0_cpld")
        self.setattr_device("urukul0_ch0")
        self.setattr_device("urukul0_ch3")         # Urukul board to control 2nd laser's AOM
        self.setattr_argument("n_cycles", NumberValue(1, precision=0, step=1))
        self.setattr_argument("green_init_duration", NumberValue(5.0 * us, precision=1, unit="us"))
        self.setattr_argument("ttl4_pulses", NumberValue(50 * ns, precision=0, unit="ns"))
        self.setattr_argument("charge_check", NumberValue(20 * us, precision=1, unit="us"))
        self.setattr_argument("full_off_resonance_sweep", BooleanValue(False))
        self.setattr_argument("after_red_op_to_mw_buffer", NumberValue(2000 * ns, unit="ns", precision=1, step=1))
        self.setattr_argument("after_mw_to_spin_readout_buffer", NumberValue(100 * ns, unit="ns", precision=1, step=1))
        self.setattr_argument("freq_resonant", NumberValue(410, precision=3, step=1))
        self.setattr_argument("freq_off_resonant", NumberValue(100, precision=3, step=1))
        self.setattr_argument('mw_gain', NumberValue(8000, precision=0, min=0, max=31000, step=1))
        self.setattr_argument("a1_optical_pump", NumberValue(5 * us, precision=2, unit="us", step=1))
        self.setattr_argument("ex_spin_readout", NumberValue(10 * us, precision=2, unit="us", step=1))
        self.setattr_argument("charge_readout", NumberValue(4 * us, precision=2, unit="us", step=1))
        self.setattr_argument("wait_time", NumberValue(500 * ns, precision=0, step=1, unit="ns"))

    def prepare_config(self, Fineres: bool = False):
        # qd.start_client('192.168.0.100') # start rfsoc client 
        # self.default_config = qd.NVConfiguration()
        # self.default_config.mw_channel = 0
        # if self.freq_resonant > 2495:
        #     self.default_config.mw_nqz = 2
        # else:
        #     self.default_config.mw_nqz = 1
        # self.default_config.mw_gain = 5000

        self.qick_tproc_clock_ns = 1/(307.2e6) #307.2Mhz is the qick clock
        self.qick_tdds_ns = self.qick_tproc_clock_ns / 16  # tdds has 16x resolution of tproc clock
        self.inherent_qick_delay_ns = 209.27*ns # inherent delay for mw pulse of qick
        self.inherent_artiq_ttl6_delay_ns = 188*ns
        self.inherent_artiq_ttl6_delay_mu = self.core.seconds_to_mu(self.inherent_artiq_ttl6_delay_ns) # inherent delay for ttl6 pulse of artiq
        self.inherent_artiq_ttl2_gate_rising_delay_ns = 77*ns
        if Fineres:
            # if self.mw_gain > 31000:
            #     print("Gain is too high for diplexer (1W max). Reduce gain or remove diplexer")
            self.inherent_artiq_qick_trigger_delay_ns = 700*ns
        else:
            # if self.mw_gain > 18000:
            #     print("Gain is too high for diplexer (1W max). Reduce gain or remove diplexer")
            self.inherent_artiq_qick_trigger_delay_ns = 377*ns

        self.inherent_artiq_ttl2_to_ttl6_delay_ns = self.inherent_artiq_ttl6_delay_ns - self.inherent_artiq_ttl2_gate_rising_delay_ns
        self.inherent_artiq_ttl2_to_ttl6_delay_mu = self.core.seconds_to_mu(self.inherent_artiq_ttl2_to_ttl6_delay_ns)
        self.ttl2_window_ns = self.inherent_artiq_qick_trigger_delay_ns + self.inherent_qick_delay_ns + 1000*ns # window to catch the trigger from rfsoc. adding 1us leeway
        self.ttl2_window_mu = self.core.seconds_to_mu(self.ttl2_window_ns)

        self.read_to_green = 190 * ns  # green delay
        self.read_to_green_mu = self.core.seconds_to_mu(self.read_to_green)
        self.green_to_red1 = 345 * ns  # red laser 1
        self.green_to_red1_mu = self.core.seconds_to_mu(self.green_to_red1)
        self.green_to_red2 = 320 * ns  # red laser 2 
        self.green_to_red2_mu = self.core.seconds_to_mu(self.green_to_red2)
        self.red2_to_red1 = self.green_to_red1 - self.green_to_red2         # red laser 2 to red laser 1 delay
        self.red2_to_red1_mu = self.core.seconds_to_mu(self.red2_to_red1)   # red laser 2 to red laser 1 delay
        self.qick_experiment_padding = 1 * us                               # padding for the experiment to prevent underflow
        self.artiq_experiment_padding = self.qick_experiment_padding - self.ttl2_window_ns/2
        self.artiq_experiment_padding_mu = self.core.seconds_to_mu(self.artiq_experiment_padding)

        self.t_buffer_us = 50 * us # increase this to prevent underflow. underflow happens due to ttl trigger from qick
        self.t_buffer_mu = self.core.seconds_to_mu(self.t_buffer_us)  # 5 us buffer min, changes depending on sequence
        self.after_artiq_recieve_trigger_delay_ns = self.t_buffer_us - self.inherent_artiq_ttl6_delay_ns
        self.after_artiq_recieve_trigger_delay_mu = self.core.seconds_to_mu(self.after_artiq_recieve_trigger_delay_ns)
        self.pulse_width_mu = self.core.seconds_to_mu(50*ns)  # ttl6 pulse width
        self.green_init_duration_mu = self.core.seconds_to_mu(self.green_init_duration)
        self.laser1_pulse_width_correction = 172 * ns
        self.laser1_pulse_width_correction_mu = self.core.seconds_to_mu(self.laser1_pulse_width_correction)
        self.laser2_pulse_width_correction = 108 * ns
        self.laser2_pulse_width_correction_mu = self.core.seconds_to_mu(self.laser2_pulse_width_correction)
        self.a1_optical_pump_correction_mu = self.core.seconds_to_mu(self.a1_optical_pump + self.laser2_pulse_width_correction)
        self.ex_spin_readout_correction_mu = self.core.seconds_to_mu(self.ex_spin_readout + self.laser1_pulse_width_correction)
        self.a1_optical_pump_mu = self.core.seconds_to_mu(self.a1_optical_pump)
        self.ex_spin_readout_mu = self.core.seconds_to_mu(self.ex_spin_readout)
        self.charge_readout_laser1_mu = self.core.seconds_to_mu(self.charge_readout + self.laser1_pulse_width_correction)
        self.charge_readout_laser2_mu = self.core.seconds_to_mu(self.charge_readout + self.laser2_pulse_width_correction)
        self.charge_readout_mu = self.core.seconds_to_mu(self.charge_readout)
        self.wait_time_mu = self.core.seconds_to_mu(self.wait_time)
        self.wait_time_laser1_mu = self.core.seconds_to_mu(self.wait_time - self.laser1_pulse_width_correction)
        self.wait_time_laser2_mu = self.core.seconds_to_mu(self.wait_time - self.laser2_pulse_width_correction)

        # calibration params 
        self.n_cycles_calibration = 10000

        self.tau_list = [] # to set the dataset with the right taus
        self.tau_list2 = [] # to use for the actual delays to concatenate delays in artiq sequence
        self.data_size = len(self.tau_list)
        self.set_dataset("on", [], broadcast=False)     # on resonance, spin readout   
        self.set_dataset("on_cr", [], broadcast=False)  # on reasonance, charge readout
        self.set_dataset("off", [], broadcast=False)    # off resonance, spin readout
        self.set_dataset("off_cr", [], broadcast=False) # off resonance, charge readout

    def run_config(self):
        self.initialize()
        # self.pulse_qick(self.default_config, freq = self.freq_resonant, full_sweep = True)
        self.set_dataset("tau", self.tau_list)
        self.temp_data_sr = [0] * self.data_size        # for spin readout
        self.temp_data_cr = [0] * self.data_size        # for charge readout
        print(self.tau_list)
        print(self.tau_list2)
        print("starting experiment: on")
        print(f"expected experiment time: {self.experiment_time_calculator()/60} minutes")
        self.tau_list2 = [self.core.seconds_to_mu(t) for t in self.tau_list2]
        self.do_pulses(freq=self.freq_resonant)
        print('on experiment done')

        # if self.full_off_resonance_sweep:
        #     self.pulse_qick(self.default_config, freq = self.freq_off_resonant, full_sweep = True)
        #     self.tau_list2 = [self.core.seconds_to_mu(t) for t in self.tau_list2]
        # else:
        #     self.temp_data_sr = [0] * 2
        #     self.temp_data_cr = [0] * 2
        #     self.data_size = 2
        #     self.pulse_qick(self.default_config, freq = self.freq_off_resonant, full_sweep = False)
        #     self.tau_list2 = [self.tau_list2[0], self.tau_list2[-1]]

        # print("starting experiment: off")
        # self.do_pulses(freq=self.freq_off_resonant)
        # print('off experiment done')

    def experiment_time_calculator(self):
        total_time = (np.sum(self.tau_list2+self.green_init_duration+self.a1_optical_pump + self.ex_spin_readout+self.charge_readout + self.artiq_experiment_padding + self.after_artiq_recieve_trigger_delay_ns)) * self.n_cycles
        return total_time

    @kernel
    def initialize(self):
        self.core.reset()
        self.ttl6.output()
        self.ttl4.output()
        self.ttl2.input()
        self.ttl4.off()  # turn off green in case its on
        self.ttl6.off()  # disable RF to NV (if previously on)
        self.urukul0_cpld.init()
        self.urukul0_ch0.init()
        self.urukul0_ch3.init()

        self.urukul0_ch0.set_frequency(50*MHz)
        self.urukul0_ch0.set_amplitude(0.05)
        self.urukul0_ch3.set_frequency(50*MHz)
        self.urukul0_ch3.set_amplitude(0.05)

        while self.ttl2.timestamp_mu(now_mu()) >= 0:
            pass
        self.core.break_realtime()
        self.core.wait_until_mu(now_mu())  # since in a different kernel from pulse sequence, make sure it finishes before start next kernel
    
    @kernel
    def do_pulses(self, freq):
        self.core.reset()
        for i in range(self.n_cycles):
            self.pulse_artiq(0, True)   
            for j in range(self.data_size-1):
                with parallel:
                    self.pulse_artiq(j+1, False)
                    self.temp_data_sr[j] = self.ttl0_counter.fetch_count()
                    self.temp_data_cr[j] = self.ttl0_counter.fetch_count()
            self.temp_data_sr[self.data_size-1] = self.ttl0_counter.fetch_count()
            self.temp_data_cr[self.data_size-1] = self.ttl0_counter.fetch_count()
            # calls an rpc to append to dataset from kernel
            if freq == self.freq_resonant:
                self.append_to_dataset("on", self.temp_data_sr)
                self.append_to_dataset("on_cr", self.temp_data_cr)
            else:
                self.append_to_dataset("off", self.temp_data_sr)
                self.append_to_dataset("off_cr", self.temp_data_cr)
            self.core.break_realtime()  # although 125ms between cycles, to prevent underflow, good to let qick and artiq relax
        self.core.wait_until_mu(now_mu())

    @kernel
    def pulse_artiq(self, index, start: bool):
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
            delay_mu(self.tau_list2[index])             # MW (includes only includes mw buffers)
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
            delay_mu(self.tau_list2[index])             # MW (includes only includes mw buffers)
            delay_mu(self.ex_spin_readout_mu)
            delay_mu(self.wait_time_laser2_mu)
            self.urukul0_ch3.sw.on()
            delay_mu(self.charge_readout_laser2_mu)
            self.urukul0_ch3.sw.off()

            at_mu(cursor)                               # green sequence
            delay_mu(self.green_to_red1_mu)
            self.ttl4.pulse_mu(self.green_init_duration_mu)
            delay_mu(self.a1_optical_pump_mu)
            delay_mu(self.tau_list2[index])             # MW sequence (includes mw buffers)                          
            
            delay_mu(self.read_to_green_mu)              # readout sequence
            self.ttl0_counter.gate_rising_mu(self.ex_spin_readout_mu)
            delay_mu(self.wait_time_mu)
            self.ttl0_counter.gate_rising_mu(self.charge_readout_mu)

            delay_mu(self.artiq_experiment_padding_mu)  # padding to prevent underflow
        else:
            print("No rfsoc trigger detected at index ", index)
            self.core.break_realtime()

