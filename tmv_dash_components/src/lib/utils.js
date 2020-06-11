import React, {useMemo} from 'react';


export function useRandomId(prefix) {
  const id = useMemo(() => {
    return `__${prefix}_${Math.random().toString(36).substr(2)}`;
  }, []);
  
  return id;
}


export function MultilineText({text}) {
  return (
    <>
      {text.split("\n").map((i, key) => <div key={key}>{i ? i : <>&nbsp;</>}</div>)}
    </>
  );
}
