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
    <table>
      <tbody>
        { stack.content.map((value, idx) => <tr key={idx}>
          <th>{decToHex(first_address + idx)}</th>
          <td>{value}</td>
          <td className="selected-memory-cell">
              { decToHex(first_address + idx) === sp ? '<SP' : null }
              { decToHex(first_address + idx) === bp ? '<BP' : null }
          </td>
        </tr>) }
      </tbody>
    </table>
  </div>;
};
