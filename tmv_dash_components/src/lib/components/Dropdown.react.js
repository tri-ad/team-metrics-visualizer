import React, {useState, useMemo, useCallback, Children} from 'react';
import PropTypes from 'prop-types';
import { Button, UncontrolledPopover, Input } from 'reactstrap';

import Checkbox from './Checkbox.react';
import CheckboxSwitch from './CheckboxSwitch.react';

import style from './Dropdown.module.scss';


function addPrefixToLabel(prefix, label) {
  if (!prefix) {
    return label;
  }

  return `${prefix} ${label}`;
}


function getVisibleOptions(options, query) {
  return query.length === 0 ? options : (
    options.filter(option => option.label.toLowerCase().includes(query.toLowerCase()))
  );
}


function DropdownPopover({id, label, options, btnLabel, searchable, children}) {
  const [query, setQuery] = useState('');
  const setQueryHandler = useCallback((e) => setQuery(e.target.value), [setQuery]);

  const visibleOptions = getVisibleOptions(options, query);

  return (<>
    <Button id={id} type="button" color='dropdown' className='d-flex'>
      {btnLabel}
      <span className="ml-3 material-icons-round">expand_more</span>
    </Button>

    <UncontrolledPopover
      hideArrow
      trigger="legacy"
      boundariesElement="window"
      placement="bottom-start"
      flip={false}
      target={id}
    >
      <div className={style.popoverBody}>
        <div className={style.popoverTitle}><h4>{label}</h4></div>

        {searchable ? <div className={style.searchBlock}>
          <Input value={query} onChange={setQueryHandler} placeholder='Search'/>
        </div> : null}
      </div>

      {children({visibleOptions})}
    </UncontrolledPopover>
  </>);
}

function DropdownOptionsSingle(props) {
  const {id, label, labelPrefix, options, value, setValue, searchable} = props;

  const selectOption = useCallback(option => {
    setValue(option.value);
  }, [setValue]);

  let btnLabel = !!value ? options.find(option => option.value === value).label : label;
  btnLabel = addPrefixToLabel(labelPrefix, btnLabel);

  return (<DropdownPopover
    id={id}
    label={label}
    searchable={searchable}
    options={options}
    btnLabel={btnLabel}
  >
    {({visibleOptions}) => (<>
      <div className={style.options}>
        {visibleOptions.map(option => (
          <div
            key={option.value}
            className={style.option}
            onClick={() => selectOption(option)}
          >
            <div>
              {option.value !== value ? (
                option.label
              ) : (
                <strong>{option.label}</strong>
              )}
            </div>
          </div>
        ))}
      </div>
    </>)}
  </DropdownPopover>);
}


function DropdownOptionsMultiple(props) {
  const {
    id, label, labelPrefix, options,
    value: values,
    setValue: setValues,
    searchable, enableSelectAll, multi
  } = props;

  const toggleOption = useCallback(option => {
    if (values.includes(option.value)) {
      setValues(values.filter(value => value !== option.value));
    } else {
      setValues([...values, option.value]);
    }
  }, [values, setValues]);

  const selectedAllOptions = useMemo(() => (
    options.every(option => values.includes(option.value))
  ), [options, values]);

  const toggleAllOptions = useCallback(() => {
    if (selectedAllOptions) {
      setValues([]);
    } else {
      setValues(options.map(option => option.value));
    }
  }, [values, setValues, selectedAllOptions]);

  let btnLabel = 'Options';
  if (selectedAllOptions || values.length === 0) {
    btnLabel = label;
  } else if (values.length === 1) {
    btnLabel = options.find(option => option.value === values[0]).label;
  } else {
    const firstOptionLabel = options.find(option => option.value === values[0]).label;
    btnLabel = `${firstOptionLabel} + ${values.length - 1}`;
  }

  btnLabel = addPrefixToLabel(labelPrefix, btnLabel);

  return (<DropdownPopover
    id={id}
    label={label}
    searchable={searchable}
    options={options}
    btnLabel={btnLabel}
  >
    {({visibleOptions}) => (<>
      <div className={style.popoverBody}>
        {enableSelectAll ? <div className={style.allOptionsBlock}>
          <div>{enableSelectAll}</div>
          <div className='ml-auto'>
            <CheckboxSwitch
              checked={selectedAllOptions}
              onChange={toggleAllOptions}
            />
          </div>
        </div> : null}
      </div>

      <div className={style.options}>
        <small className={style.optionsLabel}>{label}</small>

        {visibleOptions.map(option => (
          <div
            key={option.value}
            className={style.option}
            onClick={() => toggleOption(option)}
          >
            {multi ? <div className={style.optionCheckbox}>
              <Checkbox
                checked={values.includes(option.value)}
                onChange={() => toggleOption(option)}
              />
            </div> : null}
            <div>{option.label}</div>
          </div>
        ))}
      </div>
    </>)}
  </DropdownPopover>);
}


/**
 * Dropdown is a component to select options.
 */
export default function Dropdown(props) {
  const {id, setProps, multi} = props;

  const setValue = useCallback(newValue => {
    setProps({value: newValue});
  }, [setProps]);

  return (
    <>
      {!multi && <DropdownOptionsSingle
        id={id}
        setValue={setValue}
        {...props}
      />}

      {multi && <DropdownOptionsMultiple
        id={id}
        setValue={setValue}
        {...props}
      />}
    </>
  );
}

Dropdown.defaultProps = {
  labelPrefix: '',
  multi: false,
  enableSelectAll: '',
  searchable: false,
};

Dropdown.propTypes = {
  /**
   * The ID used to identify this component in Dash callbacks.
   */
  id: PropTypes.string,

  /**
   * Button label / placeholder
   */
  label: PropTypes.string.isRequired,

  /**
   * Prefix
   */
  labelPrefix: PropTypes.string,

  /**
   * Available options.
   */
  options: PropTypes.array.isRequired,

  /**
   * Selected option / options.
   */
  value: PropTypes.any,

  /**
   * Dash-assigned callback that should be called to report property changes
   * to Dash, to make them available for callbacks.
   */
  setProps: PropTypes.func,

  /**
   * Allow to search options.
   */
  searchable: PropTypes.bool,

  /**
   * Allow to select all options via button with prop's text
   */
  enableSelectAll: PropTypes.string,

  /**
   * Allow selecting multiple options.
   */
  multi: PropTypes.bool,
};
