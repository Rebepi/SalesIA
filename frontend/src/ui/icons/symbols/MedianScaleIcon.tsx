import React from "react";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const MedianScaleIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="fallback"
    renderPaths={() => (
      <g>
        <line x1="12" y1="3" x2="12" y2="21" />
        <rect x="4" y="9" width="16" height="6" rx="2" />
      </g>
    )}
  />
);
