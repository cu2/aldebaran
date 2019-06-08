import React from 'react';
import './Token.css';


interface Props {
  name: string;
  opcode: string;
}

export const Token: React.FunctionComponent<Props> = ({name, opcode}) => {
  return <div className="token">
    <div className="token-name">{name}</div>
    <div className="token-opcode">{opcode}</div>
  </div>;
}
