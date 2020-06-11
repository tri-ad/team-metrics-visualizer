/* eslint no-magic-numbers: 0 */
import React, {Component} from 'react';
import { Dropdown, CheckboxSwitch, Checkbox, TeamHealthTable } from '../lib';


class Wrapper extends Component {
  constructor(props) {
    super();
    this.state = {...props.initialState};
  }

  setProps = (newProps) => {
    this.setState(newProps);
  };

  render() {
    return this.props.children({state: this.state, setProps: this.setProps});
  }
}

const teams = [];
for (let i = 1; i < 15; i++) {
  teams.push({value: i, label: `Team #${i}`});
}

const teamHealthColums = [
  {
    id: 'Topic',
    headers: [
      {label: ''},
      {label: 'Topic'}
    ],
  }, {
    id: 'Team #1_2019 Q4S',
    color: '#ffffff',
    align: 'center',
    fontWeight: '900',
    headers: [
      {label: 'Team #1', align: 'center'},
      {label: '2019 Q4S', align: 'center'}
    ],
  }, {
    id: 'Team #1_2019 Q4F',
    color: '#ffffff',
    align: 'center',
    fontWeight: '900',
    headers: [
      {label: 'Team #1', align: 'center'},
      {label: '2019 Q4F', align: 'center'}
    ],
  }, {
    id: 'Team #2_2019 Q4S',
    color: '#ffffff',
    align: 'center',
    fontWeight: '900',
    headers: [
      {label: 'Team #2', align: 'center'},
      {label: '2019 Q4S', align: 'center'}
    ],
  }, {
    id: 'Team #2_2019 Q4F',
    color: '#ffffff',
    align: 'center',
    fontWeight: '900',
    headers: [
      {label: 'Team #2', align: 'center'},
      {label: '2019 Q4F', align: 'center'}
    ],
  },
]

const teamHealthData = [
  {
    'Topic': {text: 'Feedback'},
    'Team #1_2019 Q4S': {
      text: 'Yellow', infoTooltip: '', trend: null, backgroundColor: 'tmv_yellow'
    },
    'Team #1_2019 Q4F': {
      text: 'Green',
      infoTooltip: (
        'We give positive appraisals, but also provide constructive feedback ' +
        'on each other\'s unproductive behaviours. '
      ),
      trend: 1,
      trendTooltip: 'Improved',
      backgroundColor: 'tmv_green',
    },
    'Team #2_2019 Q4S': {
      text: 'Red', infoTooltip: '', trend: null, backgroundColor: 'tmv_red'
    },
    'Team #2_2019 Q4F': {
      text: 'Yellow',
      infoTooltip: '',
      trend: 1,
      trendTooltip: 'Improved',
      backgroundColor: 'tmv_yellow'
    },
  },
  {
    'Topic': {text: 'Team Work'},
    'Team #1_2019 Q4S': {
      text: 'No Data', infoTooltip: '', trend: null, backgroundColor: 'tmv_gray'
    },
    'Team #1_2019 Q4F': {
      text: 'Green',
      infoTooltip: '',
      backgroundColor: 'tmv_green',
    },
    'Team #2_2019 Q4S': {
      text: 'Yellow', infoTooltip: '', trend: null, backgroundColor: 'tmv_yellow'
    },
    'Team #2_2019 Q4F': {
      text: 'Red',
      infoTooltip: '',
      trend: -1,
      trendTooltip: 'Worsened',
      backgroundColor: 'tmv_red'
    },
  },
]


function App() {
  return (
    <div className='d-flex flex-column ml-5'>
      <div className='mt-3'>
        <h3>Team Health Table</h3>
        <Wrapper initialState={{}}>
          {({state, setProps}) => (
            <TeamHealthTable
              id='TeamHealthTable'
              columns={teamHealthColums}
              data={teamHealthData}
              merge_duplicate_headers
              setProps={setProps}
              {...state}
            />
          )}
        </Wrapper>
      </div>

      <div className='mt-3'>
        <h3>Dropdown</h3>
        <Wrapper initialState={{
          value: 5
        }}>
          {({state, setProps}) => (
            <Dropdown
              id='TeamsDropdown'
              label='Teams'
              options={teams}
              setProps={setProps}
              searchable
              {...state}
            />
          )}
        </Wrapper>
      </div>

      <div className='mt-3'>
        <h3>Dropdown multi</h3>
        <Wrapper initialState={{
          value: []
        }}>
          {({state, setProps}) => (
            <Dropdown
              id='TeamsDropdownMulti'
              label='Teams'
              options={teams}
              setProps={setProps}
              searchable
              enableSelectAll='All Teams'
              multi
              {...state}
            />
          )}
        </Wrapper>
      </div>

      <div className='mt-3'>
        <h3>Checkbox</h3>
        <Wrapper initialState={{
          checked: false
        }}>
          {({state, setProps}) => (
            <Checkbox
              setProps={setProps}
              {...state}
            />
          )}
        </Wrapper>
      </div>

      <div className='mt-3'>
        <h3>Checkbox Switch</h3>
        <Wrapper initialState={{
          checked: false
        }}>
          {({state, setProps}) => (
            <CheckboxSwitch
              setProps={setProps}
              {...state}
            />
          )}
        </Wrapper>
      </div>
    </div>
  );
}

export default App;
