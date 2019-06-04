import React from 'react';
import { hexToDec, decToHex } from './utils';


export type MemoryType = {
  first_address: string;
  last_address: string;
  content: string[];
};

interface Props {
  memory: MemoryType;
  ip: string;
};

export const Memory: React.FunctionComponent<Props> = ({memory, ip}) => {
  const headerRow = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15];
  const first_address = hexToDec(memory.first_address);
  const len = memory.content.length;
  let memoryRows = [];
  for(let idx = 0; idx < len; idx+=16) {
    memoryRows.push(memory.content.slice(idx, idx + 16));
  }
  const ipDec = hexToDec(ip);
  return <div>
    <h2>Memory</h2>
    <table>
      <tbody>
        <tr>
          <th></th>
          { headerRow.map((value, idx) => <th key={idx}>{decToHex(value)}</th>) }
        </tr>
        { memoryRows.map((row, rowIdx) => <tr key={rowIdx}>
          <th key={rowIdx}>{decToHex(first_address + rowIdx * 16).padStart(4, '0')}</th>
          { row.map((value, idx) => <td key={idx} className={
            first_address + rowIdx * 16 + idx === ipDec ? 'selected-memory-cell' : ''
          }>{value}</td>)}
        </tr>) }
      </tbody>
    </table>
  </div>;
};
