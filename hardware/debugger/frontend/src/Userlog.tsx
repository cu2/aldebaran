import React from 'react';
import './Userlog.css';


interface Props {
  userlog: string[];
};

export const Userlog: React.FunctionComponent<Props> = ({userlog}) => {
  return <div>
    <h2>Userlog</h2>
    <div className="userlog">
      { userlog.map((value, idx) => <div key={idx}>{value}</div>) }
    </div>
  </div>;
};
