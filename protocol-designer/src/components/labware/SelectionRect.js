// @flow
import * as React from 'react'
import styles from './SelectionRect.css'
import type {DragRect, GenericRect} from '../collision-types'

type Props = {
  onSelectionMove?: (e: MouseEvent, GenericRect) => mixed,
  onSelectionDone?: (e: MouseEvent, GenericRect) => mixed,
  svg?: boolean, // set true if this is an embedded SVG
  children?: React.Node,
}

type State = {
  positions: DragRect | null,
  isSelecting: boolean,
}

class SelectionRect extends React.Component<Props, State> {
  // TODO Ian 2018-02-22 No support in Flow for SVGElement yet: https://github.com/facebook/flow/issues/2332
  // this `parentRef` should be HTMLElement | SVGElement
  parentRef: ?any

  constructor (props: Props) {
    super(props)
    this.state = { positions: null, isSelecting: false }

    document.addEventListener('mousemove', this.handleMouseMove)
    document.addEventListener('mouseup', this.handleMouseUp)
  }

  componentWillUnmount () {
    document.addEventListener('mousemove', this.handleMouseMove)
    document.addEventListener('mouseup', this.handleMouseUp)
  }

  renderRect (args: DragRect) {
    const {xStart, yStart, xDynamic, yDynamic} = args
    const left = Math.min(xStart, xDynamic)
    const top = Math.min(yStart, yDynamic)
    const width = Math.abs(xDynamic - xStart)
    const height = Math.abs(yDynamic - yStart)

    if (this.props.svg) {
      // calculate ratio btw clientRect bounding box vs svg parent viewBox
      // WARNING: May not work right if you're nesting SVGs!
      const parentRef = this.parentRef
      if (!parentRef) {
        return null
      }

      const clientRect: {width: number, height: number, left: number, top: number} = parentRef.getBoundingClientRect()
      const viewBox: {width: number, height: number} = parentRef.closest('svg').viewBox.baseVal // WARNING: elem.closest() is experiemental

      const xScale = viewBox.width / clientRect.width
      const yScale = viewBox.height / clientRect.height

      return <rect
        x={(left - clientRect.left) * xScale}
        y={(top - clientRect.top) * yScale}
        width={width * xScale}
        height={height * yScale}
        className={styles.selection_rect}
      />
    }

    return <div
      className={styles.selection_rect}
      styles={{
        left: left + 'px',
        top: top + 'px',
        width: width + 'px',
        height: height + 'px',
      }}
    />
  }

  getRect (args: DragRect) {
    const {xStart, yStart, xDynamic, yDynamic} = args
    // convert internal rect position to more generic form
    // TODO should this be used in renderRect?
    return {
      x0: Math.min(xStart, xDynamic),
      x1: Math.max(xStart, xDynamic),
      y0: Math.min(yStart, yDynamic),
      y1: Math.max(yStart, yDynamic),
    }
  }

  handleMouseDown = (e: MouseEvent) => {
    this.setState({
      positions: {xStart: e.clientX, xDynamic: e.clientX, yStart: e.clientY, yDynamic: e.clientY},
      isSelecting: true,
    })
  }

  handleMouseMove = (e: MouseEvent) => {
    if (this.state.isSelecting) this.handleDrag(e)
  }

  handleDrag = (e: MouseEvent) => {
    const nextRect = {...this.state.positions, xDynamic: e.clientX, yDynamic: e.clientY}
    this.setState({ positions: nextRect })

    const rect = this.getRect(nextRect)
    this.props.onSelectionMove && this.props.onSelectionMove(e, rect)
  }

  handleMouseUp = (e: MouseEvent) => {
    if (!(e instanceof MouseEvent)) return

    const finalRect = this.state.positions && this.getRect(this.state.positions)

    // clear the rectangle
    this.setState({ positions: null, isSelecting: false })

    // call onSelectionDone callback with {x0, x1, y0, y1} of final selection rectangle
    this.props.onSelectionDone && finalRect && this.props.onSelectionDone(e, finalRect)
  }

  render () {
    const { svg, children } = this.props
    const WellElement = svg ? 'g' : 'div'
    return (
      <WellElement
        onMouseDown={this.handleMouseDown}
        ref={ref => { this.parentRef = ref }}>
        {children}
        {this.state.positions && this.renderRect(this.state.positions)}
      </WellElement>
    )
  }
}

export default SelectionRect
