import React from "react";
import { MOTION_EASINGS } from "../../motion";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const CheckIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="check"
    renderPaths={(state, isReduced) => {
      const isSuccessOrActive = state === "success" || state === "hover" || state === "focus" || state === "pressed";
      const offset = !isReduced && isSuccessOrActive ? 0 : 0;
      return (
        <path
          d="M20 6 9 17l-5-5"
          style={{
            strokeDasharray: 24,
            strokeDashoffset: offset,
            transition: isReduced ? "none" : `stroke-dashoffset 200ms ${MOTION_EASINGS.enter}`
          }}
        />
      );
    }}
  />
);
