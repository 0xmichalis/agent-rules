# Test pyramid

* **Unit tests** form the base. Cover every meaningful behavior of the code
  under test, including representative inputs, boundaries, failure paths and
  regressions. Assert observable results and use deterministic inputs and local
  doubles for slow or external dependencies. Use coverage reports to find
  untested behavior and review the assertions for each gap.
* **Integration tests** exercise the real collaborators on both sides of a
  boundary where their interaction matters. Use the narrowest useful scope,
  such as an API handler with its service, a component with its providers or a
  repository with a test database. Control dependencies outside that boundary.
* **End-to-end tests** sit at the top. Keep a few substantial user journeys
  that exercise the running application through its public entry points.
  Use controlled test data and make each journey independent. Keep the steps
  that establish that the whole journey works.
* Put each regression at the lowest level that can expose it. When a broad
  test finds a bug, add a focused regression test and keep the broad test when
  it verifies a distinct boundary or journey. Run fast tests early in CI and
  broader suites after the fast feedback.

[Martin Fowler's Test Pyramid](https://martinfowler.com/bliki/TestPyramid.html),
[The Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html),
[Test Coverage](https://martinfowler.com/bliki/TestCoverage.html)
