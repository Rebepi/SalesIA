

export function verifyBackendOperationalError(response: {
  isAvailable: boolean;
  statusCode?: number;
  errorMessage?: string;
}): {
  operationalErrorDisplayed: boolean;
  substitutedByReady: boolean;
  substitutedByDemoFigures: boolean;
  substitutedBySuccessToast: boolean;
} {
  if (!response.isAvailable || (response.statusCode && response.statusCode >= 500)) {
    return {
      operationalErrorDisplayed: true,
      substitutedByReady: false,
      substitutedByDemoFigures: false,
      substitutedBySuccessToast: false
    };
  }
  return {
    operationalErrorDisplayed: false,
    substitutedByReady: true,
    substitutedByDemoFigures: false,
    substitutedBySuccessToast: false
  };
}
