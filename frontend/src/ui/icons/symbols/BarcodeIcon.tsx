import React from "react";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const BarcodeIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="fallback"
    renderPaths={() => (
      <g>
        <path d="M3 5v14M8 5v14M12 5v14M17 5v14M21 5v14" />
      </g>
    )}
  />
);
