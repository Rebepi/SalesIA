import React from "react";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const TransferArrowsIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="fallback"
    renderPaths={() => (
      <g>
        <polyline points="17 1 21 5 17 9" />
        <path d="M3 5h18" />
        <polyline points="7 23 3 19 7 15" />
        <path d="M21 19H3" />
      </g>
    )}
  />
);
