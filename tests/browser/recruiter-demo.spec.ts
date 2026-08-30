export const recruiterBrowserScenarios=[
 {id:"conversation-success",steps:["greeting","follow-up device","follow-up symptom","remote permission","UI diagnostics","repair approval","technical verification","employee confirmation"]},
 {id:"remote-decline",steps:["reset","intake","clarification","decline","confirm no connection"]},
 {id:"failed-verification",steps:["complete repair","answer not fixed","confirm conversation continues"]},
 {id:"insights-dashboard",steps:["open service insights","verify five charts","open data table"]},
 {id:"mobile-drawer",steps:["set mobile viewport","open drawer","navigate","close on route change"]},
 {id:"keyboard-focus",steps:["tab to skip link","activate main content","tab through controls"]},
 {id:"deterministic-reset",steps:["complete partial journey","reset","verify greeting and seed"]},
] as const;
