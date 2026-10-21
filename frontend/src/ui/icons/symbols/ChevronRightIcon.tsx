import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const ChevronRightIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="chevronRight"
    renderPaths={(state, isReduced) => {
      const isActive = state === "hover" || state === "focus" || state === "pressed";
      const shift = !isReduced && isActive ? "translateX(2px)" : "translateX(0)";
      return (
        <path
          d="m9 18 6-6-6-6"
          style={{
            transform: shift,
            transition: isReduced ? "none" : `transform 140ms ${MOTION_EASINGS.standard}`
          }}
        />
      );
    }}
  />
);
