

export type FormStatus = "pristine" | "dirty" | "validating" | "submitting" | "success" | "error";

export class FormStateManager<T extends Record<string, unknown>> {
  private status: FormStatus = "pristine";
  private initialValues: T;
  private currentValues: T;
  private fieldErrors: Record<string, string> = {};
  private globalError: string | null = null;
  private validator?: (values: T) => Record<string, string> | null;
  private submitCount = 0;

  constructor(initialValues: T, validator?: (values: T) => Record<string, string> | null) {
    this.initialValues = JSON.parse(JSON.stringify(initialValues));
    this.currentValues = JSON.parse(JSON.stringify(initialValues));
    this.validator = validator;
  }

  getStatus(): FormStatus {
    return this.status;
  }

  getValues(): T {
    return this.currentValues;
  }

  getFieldErrors(): Record<string, string> {
    return { ...this.fieldErrors };
  }

  getGlobalError(): string | null {
    return this.globalError;
  }

  getSubmitCount(): number {
    return this.submitCount;
  }

  setValue<K extends keyof T>(field: K, value: T[K]): void {
    this.currentValues[field] = value;
    if (this.fieldErrors[field as string]) {
      delete this.fieldErrors[field as string];
    }
    this.status = "dirty";
  }

  setFieldError(field: string, error: string): void {
    this.fieldErrors[field] = error;
    this.status = "error";
  }

  setGlobalError(error: string): void {
    this.globalError = error;
    this.status = "error";
  }

  async submit(submitFn: (values: T) => Promise<void>): Promise<boolean> {
    if (this.status === "validating" || this.status === "submitting") {
      return false;
    }

    this.status = "validating";
    this.fieldErrors = {};
    this.globalError = null;

    if (this.validator) {
      const errors = this.validator(this.currentValues);
      if (errors && Object.keys(errors).length > 0) {
        this.fieldErrors = errors;
        this.status = "error";
        return false;
      }
    }

    this.status = "submitting";
    this.submitCount += 1;

    try {
      await submitFn(this.currentValues);
      this.status = "success";
      return true;
    } catch (err) {
      this.status = "error";
      if (err && typeof err === "object" && "detail" in err && typeof (err as { detail: string }).detail === "string") {
        this.globalError = (err as { detail: string }).detail;
      } else if (err instanceof Error) {
        this.globalError = err.message;
      } else {
        this.globalError = "Error al procesar el formulario";
      }
      return false;
    }
  }

  handleEnterKey(
    event: { preventDefault: () => void; key?: string },
    submitFn: (values: T) => Promise<void>
  ): Promise<boolean> {
    event.preventDefault();
    return this.submit(submitFn);
  }

  reset(): void {
    this.currentValues = JSON.parse(JSON.stringify(this.initialValues));
    this.fieldErrors = {};
    this.globalError = null;
    this.status = "pristine";
  }
}
