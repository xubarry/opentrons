// @flow
// calibration panel with various calibration-related controls and info

import * as React from 'react'
import { useDispatch, useSelector } from 'react-redux'

import type { Dispatch, State } from '../../types'
import * as Calibration from '../../calibration'
import { CONNECTABLE } from '../../discovery'
import type { ViewableRobot } from '../../discovery/types'
import { selectors as robotSelectors } from '../../robot'

import { useInterval, Card } from '@opentrons/components'

import {
  DECK_CAL_STATUS_POLL_INTERVAL,
  DISABLED_CANNOT_CONNECT,
  DISABLED_CONNECT_TO_ROBOT,
  DISABLED_PROTOCOL_IS_RUNNING,
} from './constants'
import { DeckCalibrationControl } from './DeckCalibrationControl'
import { CheckCalibrationControl } from './CheckCalibrationControl'

type Props = {|
  robot: ViewableRobot,
|}

const TITLE = 'Robot Calibration'

// TODO: Change these two
const BAD_DECK_CALIBRATION =
  'Bad deck calibration detected. Please perform a full deck calibration.'
const NO_DECK_CALIBRATION = 'Please perform a full deck calibration.'

export function CalibrationCard(props: Props): React.Node {
  const { robot } = props
  const { name: robotName, status } = robot
  const notConnectable = status !== CONNECTABLE

  const dispatch = useDispatch<Dispatch>()
  useInterval(
    () => dispatch(Calibration.fetchCalibrationStatus(robotName)),
    DECK_CAL_STATUS_POLL_INTERVAL,
    true
  )

  const isRunning = useSelector(robotSelectors.getIsRunning)
  const deckCalStatus = useSelector((state: State) => {
    return Calibration.getDeckCalibrationStatus(state, robotName)
  })
  const deckCalData = useSelector((state: State) => {
    return Calibration.getDeckCalibrationData(state, robotName)
  })

  let buttonDisabledReason = null
  if (notConnectable) {
    buttonDisabledReason = DISABLED_CANNOT_CONNECT
  } else if (!robot.connected) {
    buttonDisabledReason = DISABLED_CONNECT_TO_ROBOT
  } else if (isRunning) {
    buttonDisabledReason = DISABLED_PROTOCOL_IS_RUNNING
  }

  let calCheckDisabledReason = buttonDisabledReason
  if (
    deckCalStatus === Calibration.DECK_CAL_STATUS_BAD_CALIBRATION ||
    deckCalStatus === Calibration.DECK_CAL_STATUS_SINGULARITY
  ) {
    calCheckDisabledReason = BAD_DECK_CALIBRATION
  } else if (deckCalStatus === Calibration.DECK_CAL_STATUS_IDENTITY) {
    calCheckDisabledReason = NO_DECK_CALIBRATION
  }

  const buttonDisabled = Boolean(buttonDisabledReason)
  return (
    <Card title={TITLE}>
      <DeckCalibrationControl
        robotName={robotName}
        buttonDisabled={buttonDisabled}
        deckCalStatus={deckCalStatus}
        deckCalData={deckCalData}
        startLegacyDeckCalibration={() => {}}
      />
      {deckCalStatus !== null && (
        <CheckCalibrationControl
          robotName={robotName}
          disabledReason={calCheckDisabledReason}
        />
      )}
    </Card>
  )
}
