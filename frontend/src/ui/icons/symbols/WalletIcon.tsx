import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const WalletIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="wallet"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const flapShift = !isReduced && isActive ? "translateY(-1px)" : "translateY(0)";
      return (
        <g>
          <path d="M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1" />
          <path
            d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"
            style={{
              transform: flapShift,
              transition: isReduced ? "none" : `transform 220ms ${MOTION_EASINGS.standard}`
            }}
          />
        </g>
      );
    }}
  />
);
