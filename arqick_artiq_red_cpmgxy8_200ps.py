import numpy as np
from artiq.experiment import *
from copy import copy
from arqick_artiq_red_cpmg_mbp_config import ARQICK_DoPulses_Red_CPMG_Mbp


class ARQICK_red_CPMGXY8_200ps(EnvExperiment, ARQICK_DoPulses_Red_CPMG_Mbp):
    def build(self):
        self.setattr_argument("n_cpmg", NumberValue(32, precision=0, step=1))
        self.setattr_argument("pi2_duration_tdds", NumberValue(77, precision=0, step=1))
        self.setattr_argument("tau_low_tdds", NumberValue(10000, precision=0, step=1, min=500)) # theres a min delay here due to qick
        self.setattr_argument("tau_high_tdds", NumberValue(15000, precision=0, step=1))
        self.setattr_argument("tau_step_tdds", NumberValue(501, precision=0, step=1))
        self.setattr_argument("scaling_mode",EnumerationValue(["linear", "exponential"], default="linear"))
        self.setattr_argument("scaling_factor", EnumerationValue(["", "17/16", "9/8", "5/4", "3/2"], default=""))
        self.build_config()
        
    def prepare(self):
        self.prepare_config(Fineres=True)

    def run(self):
        self.run_config()

    # @rpc
    # def config_qick(self, default_config):
    #     config = copy(default_config)
    #     config.mw_gain = self.mw_gain
    #     config.freq_fMHz = self.freq_resonant
    #     config.mw_pi2_tdds = self.pi2_duration_tdds
    #     config.n_cpmg = int(self.n_cpmg) # number of cpmg xy8 rounds
    #     config.scaling_mode = "linear"

    #     # remember the sweep is inclusive of the start and end values
    #     if self.scaling_mode == "linear":
    #         config.add_unitless_linear_sweep("delay_tdds", self.tau_low_tdds, self.tau_high_tdds, delta = self.tau_step_tdds)
    #         self.tau_list = np.linspace(config.delay_tdds_start, config.delay_tdds_end, config.nsweep_points) * self.qick_tdds_ns
    #         self.tau_list2 = np.linspace(config.delay_tdds_start, config.delay_tdds_end, config.nsweep_points) * self.qick_tdds_ns
    #     else:
    #         config.add_unitless_exponential_sweep("delay_tdds", self.tau_low_tdds, self.tau_high_tdds, self.scaling_factor)
    #         self.tau_list = qd.int_exp_scale(config.delay_tdds_start, config.delay_tdds_end, self.scaling_factor) * self.qick_tdds_ns
    #         self.tau_list2 = qd.int_exp_scale(config.delay_tdds_start, config.delay_tdds_end, self.scaling_factor) * self.qick_tdds_ns
        
    #     self.tau_list2 = self.tau_list2*2*self.n_cpmg + self.after_red_op_to_mw_buffer + self.after_mw_to_spin_readout_buffer + self.pi2_duration_tdds*self.qick_tdds_ns
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
    #     prog = CPMGXY8AnyNFineRes(config)
    #     prog.run_rounds(soc, rounds=0, start_src="external")