import React, {useCallback} from 'react';
import PropTypes from 'prop-types';

import style from './Checkbox.module.scss';


export default function Checkbox({id, checked, setProps, onChange}) {
  const toggle = useCallback(e => {
    setProps && setProps({checked: !checked});
    onChange && onChange(!checked);
  }, [setProps, onChange, checked]);

  return (
    <div id={id}>
      <input
        className={style.hiddenCheckbox}
        type='checkbox'
        checked={checked}
        onChange={toggle}
      />
      <div className={style.checkbox} onClick={toggle}>
        {checked ? (
          <div className='material-icons-outlined'>check_box</div>
        ) : (
          <div className='material-icons-outlined'>check_box_outline_blank</div>
        )}
      </div>
    </div>
  );
}

Checkbox.defaultProps = {};

Checkbox.propTypes = {
  /**
   * The ID used to identify this component in Dash callbacks.
   */
  id: PropTypes.string,

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
