import React from 'react';
import { Stack, StackType } from './Stack';


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
};

export class App extends React.Component<Props, State> {
  interval?: NodeJS.Timeout;

  constructor(props: Props) {
    super(props);
    this.state = {
      online: false,
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
    this.sendRequest('/api/internal', null, (data: any) => {
      this.setState({ internal: data });
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
    if (! internal) {
      return title;
    }
    return <div>
      {title}
      <button onClick={() => this.cpuStep(1)}>STEP 1</button>
      <button onClick={() => this.cpuStep(10)}>STEP 10</button>
      <h2>CPU</h2>
      <div>cycle_count = {internal.clock.cycle_count}</div>
      <div>halt = {internal.cpu.halt ? 'HALT' : '-'}</div>
      <div>shutdown = {internal.cpu.shutdown ? 'SHUTDOWN' : '-'}</div>
      <div>IP = {internal.registers.IP}</div>
      { internal.cpu.last_instruction ? <div>
        <div>
          Last instruction @ {internal.cpu.last_ip} = {internal.cpu.last_instruction.name}
          { internal.cpu.last_instruction.operands.map((op: string, idx: number) => <span key={idx}> {op}</span>)}
        </div>
      </div> : null}
      <h2>Registers</h2>
      <div>AX = {internal.registers.AX}</div>
      <div>BX = {internal.registers.BX}</div>
      <div>CX = {internal.registers.CX}</div>
      <div>DX = {internal.registers.DX}</div>
      <div>SI = {internal.registers.SI}</div>
      <div>DI = {internal.registers.DI}</div>
      <Stack
        stack={internal.stack}
        sp={internal.registers.SP}
        bp={internal.registers.BP}
      />
    </div>;
  }
};
