import React from 'react';
import { Stack, StackType } from './Stack';
import { Memory, MemoryType } from './Memory';
import { Token } from './Token';
import { decToHex } from './utils';
import './App.css';


type InternalType = {
  registers: any;
  stack: StackType;
  cpu: any;
  clock: any;
};

interface Props {};

interface State {
  online: boolean;
  internal?: InternalType;
  memoryOffset: number;
  memory?: MemoryType;
};

export class App extends React.Component<Props, State> {
  interval?: NodeJS.Timeout;

  constructor(props: Props) {
    super(props);
    this.state = {
      online: false,
      memoryOffset: 0,
    };
    this.cpuStep = this.cpuStep.bind(this);
  }

  sendRequest(url: string, payload: object | null, cb: any) {
    const init = (payload === null) ? undefined : {
      method: 'POST',
      body: JSON.stringify(payload),
    }
    fetch(url, init)
      .then(response => {
        if (response.ok) {
          return response.json();
        }
        throw new Error('Response not ok.');
      })
      .then(data => {
        this.setState({ online: true });
        cb(data);
      })
      .catch(error => {
        this.setState({ online: false });
      });
  }

  cpuStep(stepCount: number) {
    this.sendRequest('/api/cpu/step', {step_count: stepCount}, (data: any) => {
      this.tick();
    });
  }

  tick() {
    this.sendRequest('/api/internal', null, (data: InternalType) => {
      this.setState({ internal: data });
    });
    const offsetHex = decToHex(this.state.memoryOffset);
    this.sendRequest(`/api/memory?offset=${offsetHex}`, null, (data: MemoryType) => {
      this.setState({ memory: data });
    });
  }

  componentDidMount() {
    this.tick();
    this.interval = setInterval(() => this.tick(), 3000);
  }

  componentWillUnmount() {
    if (this.interval) {
      clearInterval(this.interval);
    }
  }

  render() {
    const title = <h1>Aldebaran {this.state.online ? '': ' (offline)'}</h1>;
    const internal = this.state.internal;
    const memory = this.state.memory;
    if (! internal) {
      return title;
    }
    if (! memory) {
      return title;
    }
    return <div>
      {title}
      <div className="app-container">
        <div className="app-cpu">
          <button onClick={() => this.cpuStep(1)}>STEP 1</button>
          <button onClick={() => this.cpuStep(10)}>STEP 10</button>
          <h2>CPU</h2>
          <div>cycle_count = {internal.clock.cycle_count}</div>
          <div>halt = {internal.cpu.halt ? 'HALT' : '-'}</div>
          <div>shutdown = {internal.cpu.shutdown ? 'SHUTDOWN' : '-'}</div>
          <div>IP = {internal.registers.IP}</div>
          <h2>Next instruction @ {internal.cpu.next_ip}</h2>
          <div>
            <Token
              name={internal.cpu.next_instruction.name}
              opcode={internal.cpu.next_instruction.opcode}
            />
            { internal.cpu.next_instruction.operands.map((operand: any, idx: number) =>
              <Token
                key={idx}
                name={operand.name}
                opcode={operand.opcode}
              />
            )}
          </div>
          { internal.cpu.last_instruction ? <div>
            <h2>Last instruction @ {internal.cpu.last_ip}</h2>
            <div>
              <Token
                name={internal.cpu.last_instruction.name}
                opcode={internal.cpu.last_instruction.opcode}
              />
              { internal.cpu.last_instruction.operands.map((operand: any, idx: number) =>
                <Token
                  key={idx}
                  name={operand.name}
                  opcode={operand.opcode}
                />
              )}
            </div>
          </div> : null}
          <h2>Registers</h2>
          <div>AX = {internal.registers.AX}</div>
          <div>BX = {internal.registers.BX}</div>
          <div>CX = {internal.registers.CX}</div>
          <div>DX = {internal.registers.DX}</div>
          <div>--</div>
          <div>BP = {internal.registers.BP}</div>
          <div>SP = {internal.registers.SP}</div>
          <div>--</div>
          <div>SI = {internal.registers.SI}</div>
          <div>DI = {internal.registers.DI}</div>
        </div>
        <div className="app-stack">
          <Stack
            stack={internal.stack}
            sp={internal.registers.SP}
            bp={internal.registers.BP}
          />
        </div>
        <div className="app-memory">
          <Memory
            memory={memory}
            ip={internal.registers.IP}
          />
        </div>
      </div>
    </div>;
  }
};
