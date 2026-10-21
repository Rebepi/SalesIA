import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const CreditCardActionIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="creditCard"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const shiftStripe = !isReduced && isActive ? "translateX(1px)" : "translateX(0)";
      return (
        <g>
          <rect width="20" height="14" x="2" y="5" rx="2" />
          <line
            x1="2"
            y1="10"
            x2="22"
            y2="10"
            style={{
              transform: shiftStripe,
              transition: isReduced ? "none" : `transform 220ms ${MOTION_EASINGS.standard}`
            }}
          />
        </g>
      );
    }}
  />
);
