import React from 'react';
import { hexToDec, decToHex } from './utils';


export type StackType = {
  first_address: string;
  last_address: string;
  content: string[];
};

interface Props {
  stack: StackType;
  sp: string;
  bp: string;
};

export const Stack: React.FunctionComponent<Props> = ({stack, sp, bp}) => {
  const first_address = hexToDec(stack.first_address);
  return <div>
    <h2>Stack</h2>
    <div>SP = {sp}</div>
    <div>BP = {bp}</div>
    <table>
      <tbody>
        { stack.content.map((value, idx) => <tr key={idx}>
          <td>{decToHex(first_address + idx)}</td>
          <td>{value}</td>
          <td>
              { decToHex(first_address + idx) === sp ? '<SP' : null }
              { decToHex(first_address + idx) === bp ? '<BP' : null }
          </td>
        </tr>) }
      </tbody>
    </table>
  </div>;
};
