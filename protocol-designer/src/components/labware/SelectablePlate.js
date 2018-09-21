// @flow
// Wrap Plate with a SelectionRect.
import * as React from 'react'
import omit from 'lodash/omit'
import reduce from 'lodash/reduce'
import {
  swatchColors,
  Labware,
  LabwareLabels,
  MIXED_WELL_COLOR,
  type Channels,
} from '@opentrons/components'

import {getCollidingWells} from '../../utils'
import {SELECTABLE_WELL_CLASS} from '../../constants'
import {getWellSetForMultichannel} from '../../well-selection/utils'
import SelectionRect from '../components/SelectionRect.js'
import type {ContentsByWell, Wells} from '../labware-ingred/types'

type LabwareProps = React.ElementProps<typeof Labware>

export type Props = {
  wellContents: ContentsByWell,
  getTipProps?: $PropertyType<LabwareProps, 'getTipProps'>,
  containerType: string,
  updateSelectedWells: (Wells) => mixed,

  selectable?: boolean,

  // used by container
  containerId: string,
  pipetteChannels?: ?Channels,
}

// TODO Ian 2018-07-20: make sure '__air__' or other pseudo-ingredients don't get in here
function getFillColor (groupIds: Array<string>): ?string {
  if (groupIds.length === 0) {
    return null
  }

  if (groupIds.length === 1) {
    return swatchColors(Number(groupIds[0]))
  }

  return MIXED_WELL_COLOR
}

class SelectablePlate extends React.Component<Props, State> {
  constructor (props) {
    super(props)
    const initialSelectedWells = reduce(this.props.wellContents, (acc, well) => (
      well.highlighted ? {...acc, [well]: well} : acc
    ), {})
    this.state = {selectedWells: initialSelectedWells, highlightedWells: {}}
  }

  _getWellsFromRect = (rect: GenericRect): * => {
    const selectedWells = getCollidingWells(rect, SELECTABLE_WELL_CLASS)
    return this._wellsFromSelected(selectedWells)
  }

  _wellsFromSelected = (selectedWells: Wells): Wells => {
    // Returns PRIMARY WELLS from the selection.
    if (this.props.pipetteChannels === 8) {
      // for the wells that have been highlighted,
      // get all 8-well well sets and merge them
      const primaryWells: Wells = Object.keys(selectedWells).reduce((acc: Wells, well: string): Wells => {
        const wellSet = getWellSetForMultichannel(this.props.containerType, well)
        if (!wellSet) return acc

        const primaryWell = wellSet[0]

        return { ...acc, [primaryWell]: primaryWell }
      }, {})

      return primaryWells
    }

    // single-channel or ingred selection mode
    return selectedWells
  }

  handleSelectionMove = (e, rect) => {
    if (!e.shiftKey) {
      this.setState({highlightedWells: this._getWellsFromRect(rect)})
    }
  }
  handleSelectionDone = (e, rect) => {
    const wells = this._getWellsFromRect(rect)
    const nextSelectedWells = e.shiftKey
      ? omit(this.state.selectedWells, Object.keys(wells))
      : {...this.state.selectedWells, ...wells}
    this.setState({selectedWells: nextSelectedWells, highlightedWells: {}})
    this.props.updateSelectedWells(nextSelectedWells)
  }

  render () {
    const {
      wellContents,
      getTipProps,
      containerType,
      selectable,
    } = this.props

    const getWellProps = (wellName) => {
      const well = wellContents[wellName]

      return {
        selectable,
        wellName,

        highlighted: Object.keys(this.state.highlightedWells).includes(wellName),
        selected: Object.keys(this.state.selectedWells).includes(wellName),
        error: well.error,
        maxVolume: well.maxVolume,

        fillColor: getFillColor(well.groupIds),
      }
    }

    const labwareComponent = (
      <Labware
        labwareType={containerType}
        getWellProps={getWellProps}
        getTipProps={getTipProps} />
    )

    if (!selectable) return labwareComponent // don't wrap labwareComponent with SelectionRect

    return (
      <SelectionRect svg onSelectionMove={this.handleSelectionMove} onSelectionDone={this.handleSelectionDone}>
        {labwareComponent}
        <LabwareLabels labwareType={containerType} />
      </SelectionRect>
    )
  }
}

export default SelectablePlate
