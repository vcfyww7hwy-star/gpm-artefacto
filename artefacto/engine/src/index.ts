/**
 * index.ts — public surface of the Motor_Sens engine.
 *
 *   import { computeAll } from "./engine/src";
 *   const { derived, cases } = computeAll(inputs);   // 111 Motor columns, same order/names as motor.json
 */
export * from "./engine";
export * from "./caseDefinitions";
export * from "./inputs";

import { computeDerived, computeCase, type Inputs, type Derived, type CaseResult, type CaseParams } from "./engine";
import { buildCases } from "./caseDefinitions";

export interface ComputedCase {
  name: string;
  desc: string;
  params: CaseParams;
  result: CaseResult;
}

/** Derived globals + the 111 Motor cases computed from a full set of inputs (≈ 1–2 ms per case). */
export function computeAll(inputs: Inputs): { derived: Derived; cases: ComputedCase[] } {
  const derived = computeDerived(inputs);
  const cases = buildCases(inputs, derived).map((c) => ({ ...c, result: computeCase(inputs, derived, c.params) }));
  return { derived, cases };
}
