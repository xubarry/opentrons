import typing
from datetime import datetime
from enum import Enum
from uuid import UUID

from opentrons.calibration_storage.types import SourceType
from opentrons.hardware_control.util import DeckTransformState
from pydantic import BaseModel, Field
from opentrons.deck_calibration.endpoints import CalibrationCommand, \
    DeckCalibrationPoint
from robot_server.service.legacy.models.control import Mount
from robot_server.service.shared_models import calibration as cal_model


class DeckStart(BaseModel):
    """Force refresh the deck calibration session if one is ongoing"""
    force: bool = Field(False,
                        description="Set to true to refresh the session")


class PipetteDeckCalibration(BaseModel):
    """
    Details of the pipette the system has selected for use in deck
    calibration
    """
    mount: Mount
    model: str = \
        Field(...,
              description="The model of the pipette attached in this mount")


class DeckStartResponse(BaseModel):
    """None"""
    token: UUID =\
        Field(...,
              description="The token to send along in future deck calibration "
                          "actions")
    pipette: PipetteDeckCalibration

    class Config:
        schema_extra = {"example": {
                  "token": "1fdec5cc-234a-11ea-b24d-f2189817b27e",
                  "pipette": {
                    "mount": "right",
                    "model": "p10_single_v1.5"
                  }
                }}


class JogAxis(str, Enum):
    """The axis to jog"""
    x = "x"
    y = "y"
    z = "z"


class JogDirection(int, Enum):
    """The direction of the jog"""
    pos = 1
    neg = -1


class DeckCalibrationDispatch(BaseModel):
    token: UUID =\
        Field(..., description="The deck calibration session token")
    command: CalibrationCommand
    tipLength: typing.Optional[float] = \
        Field(None,
              description="The length of the tip you are prompting the user to"
                          " attach. Required for command \"attach tip\"")
    point: typing.Optional[DeckCalibrationPoint] = \
        Field(None,
              description="Required for commands \"save xy\" and \"move\"")
    axis: typing.Optional[JogAxis] = \
        Field(None,
              description="The axis to jog. Required for \"jog\" command.")
    direction: typing.Optional[JogDirection] =\
        Field(None,
              description="The direction to jog. Required for \"jog\" "
                          "command.")
    step: typing.Optional[float] =\
        Field(None,
              description="The distance to jog. Required for \"jog\" command.")

    class Config:
        schema_extra = {"examples": {
                "jog": {
                  "description": "Jog +1mm in X",
                  "value": {
                    "command": "jog",
                    "token": "1fdec5cc-234a-11ea-b24d-f2189817b27e",
                    "axis": "x",
                    "direction": 1,
                    "step": 1
                  }
                },
                "move": {
                  "description": "Move to cross 1",
                  "value": {
                    "command": "move",
                    "token": "1fdec5cc-234a-11ea-b24d-f2189817b27e",
                    "point": "1"
                  }
                },
                "savexy": {
                  "description": "Save the XY position of cross 2 (in slot 3)",
                  "value": {
                    "command": "save xy",
                    "token": "1fdec5cc-234a-11ea-b24d-f2189817b27e",
                    "point": "2"
                  }
                },
                "attachTip": {
                  "description": "Inform the OT-2 that a tip is attached",
                  "value": {
                    "command": "attach tip",
                    "token": "1fdec5cc-234a-11ea-b24d-f2189817b27e",
                    "tipLength": 51.7
                  }
                },
                "detachTip": {
                  "description": "Inform the OT-2 that a tip has been removed",
                  "value": {
                    "command": "detach tip",
                    "token": "1fdec5cc-234a-11ea-b24d-f2189817b27e"
                  }
                },
                "saveZ": {
                  "description": "Save the current Z position as the height of"
                                 " the deck",
                  "value": {
                    "command": "save z",
                    "token": "1fdec5cc-234a-11ea-b24d-f2189817b27e"
                  }
                },
                "saveTransform": {
                  "description": "Save the current transform after saving all "
                                 "positions",
                  "value": {
                    "command": "save transform",
                    "token": "1fdec5cc-234a-11ea-b24d-f2189817b27e"
                  }
                },
                "release": {
                  "description": "End the deck calibration session",
                  "value": {
                    "command": "release",
                    "token": "1fdec5cc-234a-11ea-b24d-f2189817b27e"
                  }
                }
              }}


Offset = typing.Tuple[float, float, float]

AffineMatrix = typing.Tuple[
  typing.Tuple[float, float, float, float],
  typing.Tuple[float, float, float, float],
  typing.Tuple[float, float, float, float],
  typing.Tuple[float, float, float, float]]

AttitudeMatrix = typing.Tuple[
  typing.Tuple[float, float, float],
  typing.Tuple[float, float, float],
  typing.Tuple[float, float, float]]


class InstrumentOffset(BaseModel):
    single: Offset
    multi: Offset


class InstrumentCalibrationStatus(BaseModel):
    right: InstrumentOffset
    left: InstrumentOffset


class MatrixType(str, Enum):
    """The deck calibration matrix type"""
    affine = 'affine'
    attitude = 'attitude'


class DeckCalibrationData(BaseModel):
    type: MatrixType = \
        Field(...,
              description="The type of deck calibration matrix:"
                          "affine or attitude")
    matrix: typing.Union[AffineMatrix, AttitudeMatrix] = \
        Field(...,
              description="The deck calibration transform matrix")
    lastModified: typing.Optional[datetime] = \
        Field(None,
              description="When this calibration was last modified")
    pipetteCalibratedWith: typing.Optional[str] = \
        Field(None,
              description="The ID of the pipette used in this calibration")
    tiprack: typing.Optional[str] = \
        Field(None,
              description="The sha256 hash of the tiprack used in this"
                          "calibration")
    source: SourceType = \
        Field(None,
              description="The calibration source")
    status: cal_model.CalibrationStatus = \
        Field(None, description="The status of this calibration as determined"
                                "by a user performing calibration check.")


class DeckCalibrationStatus(BaseModel):
    status: DeckTransformState = \
        Field(...,
              description="An enum stating whether a user has a valid robot"
                          "deck calibration. See DeckTransformState"
                          "class for more information.")
    data: DeckCalibrationData = \
        Field(...,
              description="Deck calibration data")


class CalibrationStatus(BaseModel):
    """The calibration status"""
    deckCalibration: DeckCalibrationStatus
    instrumentCalibration: InstrumentCalibrationStatus
