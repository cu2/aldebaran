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
  }

  tick() {
    fetch('/api/internal')
      .then(response => {
        if (response.ok) {
          return response.json();
        }
        throw new Error('Reponse not ok.');
      })
      .then(data => {
        this.setState({
          online: true,
          internal: data,
        });
      })
      .catch(error => {
        this.setState({ online: false });
      });
  }

  componentDidMount() {
    this.interval = setInterval(() => this.tick(), 100);
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
      <h2>Clock</h2>
      <div>cycle_count = {internal.clock.cycle_count}</div>
      <h2>CPU</h2>
      <div>halt = {internal.cpu.halt ? 'HALT' : '-'}</div>
      <div>shutdown = {internal.cpu.shutdown ? 'SHUTDOWN' : '-'}</div>
      <h3>Instruction</h3>
        <div>IP = {internal.registers.IP}</div>
        { internal.cpu.current_instruction ? <div>
          <div>name = {internal.cpu.current_instruction.name}</div>
          <div>operands = {internal.cpu.current_instruction.operands}</div>
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
