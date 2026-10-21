import React from "react";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const TrendDownIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="fallback"
    renderPaths={() => (
      <g>
        <polyline points="23 18 13.5 8.5 8.5 13.5 1 6" />
        <polyline points="17 18 23 18 23 12" />
      </g>
    )}
  />
);
