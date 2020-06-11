import React from 'react';
import PropTypes from 'prop-types';
import { UncontrolledTooltip } from 'reactstrap';
import { useRandomId, MultilineText } from '../utils';

import style from './TeamHealthTable.module.scss';


const TMV_COLORS = {
  'tmv_red': 'var(--red-400)',
  'tmv_yellow': 'var(--yellow-300)',
  'tmv_green': 'var(--green-400)',
  'tmv_gray': 'var(--gray-400)',
};

const TMV_TREND_COLORS = {
  'tmv_red': {backgroundColor: 'var(--red-500)', color: 'var(--red-100)'},
  'tmv_yellow': {backgroundColor: 'var(--yellow-400)', color: 'var(--yellow-100)'},
  'tmv_green': {backgroundColor: 'var(--green-500)', color: 'var(--green-100)'},
};

function CellTrend({trend, trendTooltip, backgroundColor}) {
  const triggerId = useRandomId('TeamHealthTable_CellTrend');

  if (trend !== -1 && trend !== 1) return null;

  const trendStyle = TMV_TREND_COLORS[backgroundColor] || {};

  return (
    <div
      className={style.cellTrendIcon}
      style={trendStyle}
      id={triggerId}
    >
      <div className={trend < 0 ? style.arrowDown : ''}>
        <span className='material-icons-round'>call_made</span>
      </div>
      {trendTooltip && <UncontrolledTooltip target={triggerId} hideArrow>
        <MultilineText text={trendTooltip}/>
      </UncontrolledTooltip>}
    </div>
  );
}

function CellInfo({infoTooltip}) {
  const triggerId = useRandomId('TeamHealthTable_CellInfo');

  if (!infoTooltip) return null;

  return (
    <div className={style.cellInfoIcon} id={triggerId}>
      <div className='material-icons-outlined'>info</div>
      <UncontrolledTooltip target={triggerId} hideArrow>
        <MultilineText text={infoTooltip}/>
      </UncontrolledTooltip>
    </div>
  );
}

function Cell({column, cell}) {
  const {text, trend, trendTooltip, infoTooltip, textColor, backgroundColor} = cell;

  const cellStyle = {};

  if (column.color) cellStyle.color = column.color;
  if (textColor) {
    const redefinedColor = TMV_COLORS[textColor];
    cellStyle.color = redefinedColor ? redefinedColor : textColor;
  }

  if (backgroundColor) {
    const redefinedColor = TMV_COLORS[backgroundColor];
    cellStyle.backgroundColor = redefinedColor ? redefinedColor : backgroundColor;
  }

  if (column.fontWeight) cellStyle.fontWeight = column.fontWeight;
  if (column.align) cellStyle.textAlign = column.align;

  return (
    <td className={style.cell} style={cellStyle}>
      <CellTrend
        trend={trend}
        trendTooltip={trendTooltip}
        backgroundColor={backgroundColor}
      />

      <div>{text}</div>

      <CellInfo infoTooltip={infoTooltip}/>
    </td>
  );
}

function Row({columns, data}) {
  return (
    <tr>
      {data.map((cell, cellIndex) => <Cell
        key={cellIndex}
        column={columns[cellIndex]}
        cell={cell}
      />)}
    </tr>
  );
}

function getHeaderRowsFromColumns(columns, merge_duplicate_headers) {
  const headerRows = [];

  if (!columns.length) return [];

  for (let rowIndex = 0; rowIndex < columns[0].headers.length; rowIndex++) {
    const headerRow = [];
    let previousLabel = null;
    let nonDupRow = null;

    for (let colIndex = 0; colIndex < columns.length; colIndex++) {
      const currentData = columns[colIndex].headers[rowIndex];

      let currentLabel = currentData.label;

      if (merge_duplicate_headers && currentLabel === previousLabel) {
        if (nonDupRow !== null) {
          nonDupRow.colSpan += 1;
        }
      } else {
        let newRow = {
          ...currentData,
          colSpan: 1
        };
        headerRow.push(newRow);
        nonDupRow = newRow;
      }

      previousLabel = currentLabel;
    }
    headerRows.push(headerRow);
  }

  return headerRows;
}

function Header({columns, merge_duplicate_headers}) {
  const headerRows = getHeaderRowsFromColumns(columns, merge_duplicate_headers);

  return (
    <thead>
      {headerRows.map((headerRow, headerRowIndex) => <tr key={headerRowIndex}>
        {headerRow.map((column, columnIndex) => <th
          key={columnIndex}
          colSpan={column.colSpan}
          style={{textAlign: column.align}}
        >
          {column.label}
        </th>)}
      </tr>)}
    </thead>
  );
}

export default function TeamHealthTable(props) {
  const {id, columns, data, merge_duplicate_headers, setProps, onChange} = props;
  const columnIds = columns.map(col => col.id);

  return (
    <table id={id} className={style.table}>
      <Header
        columns={columns}
        merge_duplicate_headers={merge_duplicate_headers}
      />
      <tbody>
        {data.map((row, rowIndex) => <Row
          key={rowIndex}
          columns={columns}
          data={columnIds.map(columnId => row[columnId])}
        />)}
      </tbody>
    </table>
  );
}

TeamHealthTable.defaultProps = {
  merge_duplicate_headers: false,
};

TeamHealthTable.propTypes = {
  /**
   * The ID used to identify this component in Dash callbacks.
   */
  id: PropTypes.string,

  /**
   * Columns
   */
  columns: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,

    color: PropTypes.string,
    align: PropTypes.string,
    fontWeight: PropTypes.string,

    headers: PropTypes.arrayOf(PropTypes.shape({
      label: PropTypes.string.isRequired,
      align: PropTypes.string,
    })).isRequired,
  })).isRequired,

  /**
   * The contents of the table.
   * The keys of each item in data should match the column IDs.
   * Each item can have these keys:
   * `text` - text content of cell
   * `infoTooltip` - info icon tooltip text
   * `trend` - `-1` for down and `1` for up 
   * `trendTooltip` - tooltip text of trend
   * `textColor` - cell text color
   * `backgroundColor` - cell background color
   */
  data: PropTypes.arrayOf(PropTypes.object).isRequired,

  /**
   * Dash-assigned callback that should be called to report property changes
   * to Dash, to make them available for callbacks.
   */
  merge_duplicate_headers: PropTypes.bool,

  /**
   * Dash-assigned callback that should be called to report property changes
   * to Dash, to make them available for callbacks.
   */
  setProps: PropTypes.func,

  /**
   * To handle changes in React code without setProps
   */
  onChange: PropTypes.func,
};
