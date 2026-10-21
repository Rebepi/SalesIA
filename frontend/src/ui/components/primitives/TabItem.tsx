import React from "react";

export interface TabItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  isDirty?: boolean;
}
