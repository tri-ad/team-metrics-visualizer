import React, {useCallback} from 'react';
import PropTypes from 'prop-types';

import { useRandomId } from '../utils';

import style from './CheckboxSwitch.module.scss';


export default function CheckboxSwitch({id, label, checked, setProps, onChange}) {
  const inputId = useRandomId('CheckboxSwitch_InputId');

  const toggle = useCallback(e => {
    setProps && setProps({checked: !checked});
    onChange && onChange(!checked);
  }, [setProps, onChange, checked]);

  return (
    <div id={id}>
      <input
        id={inputId}
        className={style.switch}
        type='checkbox'
        checked={checked}
        onChange={toggle}
      />
      <label for={inputId}>{label}</label>
    </div>
  );
}

CheckboxSwitch.defaultProps = {
  label: '',
};

CheckboxSwitch.propTypes = {
  /**
   * The ID used to identify this component in Dash callbacks.
   */
  id: PropTypes.string,

  label: PropTypes.string,

  /**
   * The value displayed in the input.
   */
  checked: PropTypes.bool,

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
