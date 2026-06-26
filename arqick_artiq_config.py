from artiq.experiment import *
import numpy as np
import smtplib
# import qickdawg as qd


class ARQICK_DoPulses:
    kernel_invariants = {"data_size", 
                         "inherent_artiq_ttl2_to_ttl6_delay_mu", 
                         "ttl2_window_mu", 
                         "after_artiq_recieve_trigger_delay_mu",
                         "tau_list2",
                         "read_to_green_mu",
                         "artiq_experiment_padding_mu",
                         "temp_data",
                         "pulse_width_mu",
                         "green_init_duration_mu",
                         "counting_duration_mu",
                        }
    
    def build_config(self):
        self.setattr_device("core")
        self.setattr_device("ttl6") # output to rfsoc
        self.setattr_device("ttl2") #input trigger to artiq
        self.setattr_device("ttl4") # green laser
        self.setattr_argument("counting_duration", NumberValue(380 * ns, precision=0, unit="ns", step=1)) # update counting duration for default value
        self.setattr_argument("n_cycles", NumberValue(100000, precision=0, step=1))
        self.setattr_argument("green_init_duration", NumberValue(1.0 * us, precision=1, unit="us"))
        self.setattr_argument("send_email", StringValue(None))
        self.setattr_argument("full_off_resonance_sweep", BooleanValue(False))
        self.setattr_argument("after_green_init_to_mw_buffer", NumberValue(2000*ns, unit = "ns", precision=1, step=1)) # for NV signlet
        self.setattr_argument("after_mw_to_readout_buffer", NumberValue(100*ns, unit = "ns", precision=1, step=1))
        self.setattr_argument("freq_resonant", NumberValue(1406.25, precision=3, step=1))
        self.setattr_argument("freq_off_resonant", NumberValue(1100, precision=3, step=1))
        self.setattr_argument('mw_gain', NumberValue(15000, precision=0, min=0, max=31000, step=1))


    def prepare_config(self, Fineres: bool = False):
        qd.start_client('128.95.31.224') # start rfsoc client 
        self.default_config = qd.NVConfiguration()
        self.default_config.mw_channel = 0
        self.default_config.mw_nqz = 1
        self.default_config.mw_gain = 5000

        self.qick_tproc_clock_ns = 1/(307.2e6) #307.2Mhz is the qick clock
        self.qick_tdds_ns = self.qick_tproc_clock_ns / 16  # tdds has 16x resolution of tproc clock
        self.inherent_qick_delay_ns = 209.27*ns # inherent delay for mw pulse of qick
        self.inherent_artiq_ttl6_delay_ns = 188*ns
        self.inherent_artiq_ttl6_delay_mu = self.core.seconds_to_mu(self.inherent_artiq_ttl6_delay_ns) # inherent delay for ttl6 pulse of artiq
        self.inherent_artiq_ttl2_gate_rising_delay_ns = 77*ns
        if Fineres:
            if self.mw_gain > 31000:
                raise ValueError("Gain is too high for diplexer (1W max). Reduce gain or remove diplexer")
            self.inherent_artiq_qick_trigger_delay_ns = 700*ns
        else:
            if self.mw_gain > 18000:
                raise ValueError("Gain is too high for diplexer (1W max). Reduce gain or remove diplexer")
            self.inherent_artiq_qick_trigger_delay_ns = 377*ns
        self.inherent_artiq_ttl2_to_ttl6_delay_ns = self.inherent_artiq_ttl6_delay_ns - self.inherent_artiq_ttl2_gate_rising_delay_ns
        self.inherent_artiq_ttl2_to_ttl6_delay_mu = self.core.seconds_to_mu(self.inherent_artiq_ttl2_to_ttl6_delay_ns)
        self.ttl2_window_ns = self.inherent_artiq_qick_trigger_delay_ns + self.inherent_qick_delay_ns + 1000*ns # window to catch the trigger from rfsoc. adding 1us leeway
        self.ttl2_window_mu = self.core.seconds_to_mu(self.ttl2_window_ns)

        self.read_to_green = 190 * ns  # green delay
        self.read_to_green_mu = self.core.seconds_to_mu(self.read_to_green)
        self.qick_experiment_padding = 1 * us  # padding for the experiment to prevent underflow
        self.artiq_experiment_padding = self.qick_experiment_padding - self.ttl2_window_ns/2
        self.artiq_experiment_padding_mu = self.core.seconds_to_mu(self.artiq_experiment_padding)

        self.t_buffer_us = 50 * us # increase this to prevent underflow. underflow happens due to ttl trigger from qick
        self.t_buffer_mu = self.core.seconds_to_mu(self.t_buffer_us)  # 5 us buffer min, changes depending on sequence
        self.after_artiq_recieve_trigger_delay_ns = self.t_buffer_us - self.inherent_artiq_ttl6_delay_ns
        self.after_artiq_recieve_trigger_delay_mu = self.core.seconds_to_mu(self.after_artiq_recieve_trigger_delay_ns)
        self.pulse_width_mu = self.core.seconds_to_mu(50*ns)  # ttl6 pulse width
        self.green_init_duration_mu = self.core.seconds_to_mu(self.green_init_duration)
        self.counting_duration_mu = self.core.seconds_to_mu(self.counting_duration)

        self.tau_list = [] # to set the dataset with the right taus
        self.tau_list2 = [] # to use for the actual delays to concatenate delays in artiq sequence
        self.data_size = len(self.tau_list)
        self.set_dataset("on", [], broadcast=False)
        self.set_dataset("off", [], broadcast=False)

    def run_config(self):
        self.initialize()

        self.pulse_qick(self.default_config, freq = self.freq_resonant, full_sweep = True)
        self.set_dataset("tau", self.tau_list)
        self.temp_data = [0] * self.data_size
        print(self.tau_list)
        print("starting experiment: on")
        self.tau_list2 = [self.core.seconds_to_mu(t) for t in self.tau_list2]
        self.do_pulses(freq=self.freq_resonant)
        print('on experiment done')

        if self.full_off_resonance_sweep:
            self.pulse_qick(self.default_config, freq = self.freq_off_resonant, full_sweep = True)
            self.tau_list2 = [self.core.seconds_to_mu(t) for t in self.tau_list2]
        else:
            self.temp_data = [0] * 2
            self.data_size = 2
            self.pulse_qick(self.default_config, freq = self.freq_off_resonant, full_sweep = False)
            self.tau_list2 = [self.tau_list2[0], self.tau_list2[-1]]

        print("starting experiment: off")
        self.do_pulses(freq=self.freq_off_resonant)
        print('off experiment done')

    @kernel
    def initialize(self):
        self.core.reset()
        self.ttl6.output()
        self.ttl4.output()
        self.ttl2.input()
        self.ttl4.off()  # turn off green in case its on
        self.ttl6.off()  # disable RF to NV (if previously on)       
        while self.ttl2.timestamp_mu(now_mu()) >= 0:
            pass
        self.core.break_realtime() 
        self.core.wait_until_mu(now_mu()) # since in a different kernel from pulse sequence, make sure it finishes before start next kernel

    @kernel
    def do_pulses(self, freq):
        self.core.reset()
        for i in range(self.n_cycles):
            self.pulse_artiq(0, True)   
            for j in range(self.data_size-1):
                with parallel:
                    self.pulse_artiq(j+1, False)
                    self.temp_data[j] = self.ttl0_counter.fetch_count()
            self.temp_data[self.data_size-1] = self.ttl0_counter.fetch_count()
            # calls an rpc to append to dataset from kernel
            if freq == self.freq_resonant:
                self.append_to_dataset("on", self.temp_data)
            else:
                self.append_to_dataset("off", self.temp_data)
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
            delay_mu(self.after_artiq_recieve_trigger_delay_mu)
            cursor = now_mu()
            self.ttl4.pulse_mu(self.green_init_duration_mu) # green init
            at_mu(cursor)
            delay_mu(self.tau_list2[index])                 # includes green init + b4 + aftr mw delays 
            cursor = now_mu()                               # bring cursor after (mw + delays)
            self.ttl4.pulse_mu(self.counting_duration_mu)   # readout
            at_mu(cursor)
            delay_mu(self.read_to_green_mu)
            self.ttl0_counter.gate_rising_mu(self.counting_duration_mu)
            delay_mu(self.artiq_experiment_padding_mu)      # padding to prevent underflow
        else:
            print("No rfsoc trigger detected at index ", index)
            self.core.break_realtime()