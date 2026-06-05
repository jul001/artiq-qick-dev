import numpy as np
from artiq.experiment import *
from copy import copy
from arqick_artiq_red_mbi_config import ARQICK_DoPulses_Red_Mbi


class ARQICK_red_rabi_mbi_200ps(EnvExperiment, ARQICK_DoPulses_Red_Mbi):
    def build(self):
        self.setattr_argument("mw_duration_low_tdds", NumberValue(500, precision=0, step=1))
        self.setattr_argument("mw_duration_high_tdds", NumberValue(1000, precision=0, step=1))
        self.setattr_argument("mw_duration_step_tdds", NumberValue(100, precision=0, step=1))
        self.build_config()

    def prepare(self):
        self.prepare_config(Fineres=True)

    def run(self):
        self.run_config()

    # @rpc
    # def pulse_qick_mbi(self, default_config, freq, full_sweep=False):
    #     soc = qd.soc
    #     config = copy(default_config)
    #     config.mw_gain = self.mw_gain
    #     config.freq_fMHz = freq

    #     if full_sweep:
    #         config.add_unitless_linear_sweep("mw_duration_tdds", self.mw_duration_low_tdds, self.mw_duration_high_tdds, delta=self.mw_duration_step_tdds)
    #         self.tau_list = np.linspace(config.mw_duration_tdds_start, config.mw_duration_tdds_end, config.nsweep_points) * self.qick_tdds_ns
    #         self.data_size = len(self.tau_list)

    #         self.tau_list2 = np.linspace(config.mw_duration_tdds_start, config.mw_duration_tdds_end, config.nsweep_points) * self.qick_tdds_ns
    #         self.tau_list2 = self.tau_list2 + self.after_red_op_to_mw_buffer + self.after_mw_to_spin_readout_buffer
    #     else:
    #         config.add_unitless_linear_sweep("mw_duration_tdds", self.mw_duration_low_tdds, self.mw_duration_high_tdds, delta=self.mw_duration_high_tdds - self.mw_duration_low_tdds)

    #     config.pulse_seq_delay_tus = round(self.delay_after_prep_nv * 1e6 +self.after_mw_to_spin_readout_buffer * 1e6 + self.read_to_red1 * 1e6 + self.ex_spin_readout * 1e6 + self.wait_time * 1e6 + self.charge_readout * 1e6 - 1.2, 5)  # after delay | the delay after qick pulses
    #     config.reps = 1
    #     config.pmod_out_pin = 0
    #     config.pmod_out_pulse_width_tns = 300
    #     config.adc_channel = 0
    #     config.readout_threshold = 8000
    #     config.readout_integration_tns = 1000
    #     config.eight_micro_delay_tus = 13

    #     config.inherent_artiq_qick_trigger_delay_tns = 700
    #     # config.delay_after_readout_window_to_mw_tus = round((self.a1_optical_pump * 1e6 + self.after_red_op_to_mw_buffer * 1e6), 5) 
    #     config.delay_after_readout_window_to_mw_tus = round((self.delay_after_ttl5_pulse_us * 1e6 + self.a1_optical_pump * 1e6 
    #                                                          + self.after_red_op_to_mw_buffer * 1e6 - self.ttl5_pulse_width_us * 1e6), 5) 
    #     config.inherent_trigger_to_pulses_delay_tns = 48645 #self.inherent_qick_delay_ns * 1e9
    #     # config.delay_before_readout_repeats_tus = round((self.green_init_duration * 1e6 + self.charge_readout * 1e6 + self.delay_after_prep_nv * 1e6 -0.605), 5)
    #     config.delay_before_readout_repeats_tus = round((self.green_init_duration * 1e6 + self.charge_readout * 1e6 
    #                                                      + self.delay_after_prep_nv * 1e6 - config.inherent_artiq_qick_trigger_delay_tns / 1000), 5)
    #     config.delay_to_line_up_with_artiq_tus = round((config.eight_micro_delay_tus + self.green_init_duration * 1e6 + self.charge_readout * 1e6 
    #                                                      + self.delay_after_prep_nv * 1e6 - config.inherent_artiq_qick_trigger_delay_tns / 1000), 5)
    #     config.pmod_out_trig_delay_tus = round((self.fixed_t_buffer_us * 1e6 + self.a1_optical_pump * 1e6 
    #                                             + self.after_red_op_to_mw_buffer * 1e6 - config.inherent_trigger_to_pulses_delay_tns / 1000), 5)  # before delay |the delay before qick pulses | to account for inherent delay for mw pulse to come out
    #     prog = RabiMbiFineRes(config)
    #     prog.run_rounds(soc, rounds=0, start_src="external")

    