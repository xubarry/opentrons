from typing import Dict

from robot_server.service.session.models.command import (
    CommandDefinition, CalibrationCommand)
from robot_server.robot.calibration.util import (
    SimpleStateMachine, StateTransitionError)
from .constants import (
    PipetteOffsetCalibrationState as POCState,
    PipetteOffsetWithTipLengthCalibrationState as POWTState)


PIP_OFFSET_CAL_TRANSITIONS: Dict[POCState, Dict[CommandDefinition, POCState]] = {
    POCState.sessionStarted: {
        CalibrationCommand.load_labware: POCState.labwareLoaded
    },
    POCState.labwareLoaded: {
        CalibrationCommand.move_to_tip_rack: POCState.preparingPipette,
    },
    POCState.preparingPipette: {
        CalibrationCommand.jog: POCState.preparingPipette,
        CalibrationCommand.pick_up_tip: POCState.inspectingTip,
    },
    POCState.inspectingTip: {
        CalibrationCommand.invalidate_tip: POCState.preparingPipette,
        CalibrationCommand.move_to_deck: POCState.joggingToDeck,
    },
    POCState.joggingToDeck: {
        CalibrationCommand.jog: POCState.joggingToDeck,
        CalibrationCommand.save_offset: POCState.joggingToDeck,
        CalibrationCommand.move_to_point_one: POCState.savingPointOne,
    },
    POCState.savingPointOne: {
        CalibrationCommand.jog: POCState.savingPointOne,
        CalibrationCommand.save_offset: POCState.calibrationComplete,
    },
    POCState.calibrationComplete: {
        CalibrationCommand.move_to_tip_rack: POCState.calibrationComplete,
    },
    POCState.WILDCARD: {
        CalibrationCommand.exit: POCState.sessionExited
    }
}

PIP_OFFSET_WITH_TL_TRANSITIONS: Dict[POWTState, Dict[CommandDefinition, POWTState]] = {
    POWTState.sessionStarted: {
        CalibrationCommand.set_has_calibration_block: POWTState.sessionStarted,
        CalibrationCommand.load_labware: POWTState.labwareLoaded
    },
    POWTState.labwareLoaded: {
        CalibrationCommand.move_to_reference_point: POWTState.measuringNozzleOffset
    },
    POWTState.measuringNozzleOffset: {
        CalibrationCommand.save_offset: POWTState.measuringNozzleOffset,
        CalibrationCommand.jog: POWTState.measuringNozzleOffset,
        CalibrationCommand.move_to_tip_rack: POWTState.preparingPipette
    },
    POWTState.preparingPipette: {
        CalibrationCommand.jog: POWTState.preparingPipette,
        CalibrationCommand.pick_up_tip: POWTState.inspectingTip,
    },
    POWTState.inspectingTip: {
        CalibrationCommand.invalidate_tip: POWTState.preparingPipette,
        CalibrationCommand.move_to_reference_point: POWTState.measuringTipOffset,
    },
    POWTState.measuringTipOffset: {
        CalibrationCommand.jog: POWTState.measuringTipOffset,
        CalibrationCommand.save_offset: POWTState.tipLengthComplete
    },
    POWTState.tipLengthComplete: {
        CalibrationCommand.move_to_deck: POWTState.joggingToDeck,
    },
    POWTState.joggingToDeck: {
        CalibrationCommand.jog: POWTState.joggingToDeck,
        CalibrationCommand.save_offset: POWTState.joggingToDeck,
        CalibrationCommand.move_to_point_one: POWTState.savingPointOne,
    },
    POWTState.savingPointOne: {
        CalibrationCommand.jog: POWTState.savingPointOne,
        CalibrationCommand.save_offset: POWTState.calibrationComplete,
    },
    POWTState.calibrationComplete: {
        CalibrationCommand.move_to_tip_rack: POWTState.calibrationComplete,
    },
    POWTState.WILDCARD: {
        CalibrationCommand.exit: POWTState.sessionExited
    }
}


class PipetteOffsetCalibrationStateMachine:
    def __init__(self):
        self._state_machine = SimpleStateMachine(
            states=set(s for s in POCState),
            transitions=PIP_OFFSET_CAL_TRANSITIONS
        )

    def get_next_state(self, from_state: POCState, command: CommandDefinition):
        next_state = self._state_machine.get_next_state(from_state, command)
        if next_state:
            return next_state
        else:
            raise StateTransitionError(command, from_state)

class PipetteOffsetWithTipLengthStateMachine:
    def __init__(self):
        self._state_amchine = SimpleStateMachine(
            states=set(s for s in POWTState),
            transitions=PIP_OFFSET_WITH_TL_TRANSITIONS,
        )

    def get_next_state(self, from_state: POWTState, command: CommandDefinition):
        next_state = self._state_machine.get_next_state(from_state, command)
        if next_state:
            return next_state
        else:
            raise StateTransitionError(command, from_state)
