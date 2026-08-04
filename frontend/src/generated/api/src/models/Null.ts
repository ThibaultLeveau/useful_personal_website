/* tslint:disable */
/* eslint-disable */
/** OpenAPI 3.1 null-only schema omitted by the pinned generator. */
export type Null = null;

export function NullFromJSON(json: any): Null {
  return NullFromJSONTyped(json, false);
}

export function NullFromJSONTyped(json: any, _ignoreDiscriminator: boolean): Null {
  return json === null ? null : null;
}

export function NullToJSON(_value?: Null | null): null {
  return null;
}

export function NullToJSONTyped(_value?: Null | null, _ignoreDiscriminator: boolean = false): null {
  return null;
}
