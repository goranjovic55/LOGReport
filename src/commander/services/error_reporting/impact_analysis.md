# Error Reporting Impact Analysis

This document analyzes the impact of the error reporting refactoring and defines the required test coverage.

## Current State

### Error Reporting Consumers
The following modules currently use error reporting functionality:

1. **src/commander/main_window.py**
   - Creates `ErrorHandler` instance
   - Impact: Need to update instantiation to use new error reporting system

2. **src/commander/presenters/commander_presenter.py**
   - Contains `_report_error` method
   - Calls `_report_error` in error handling scenarios
   - Impact: Need to update to use new error reporting system

3. **src/commander/services/commander_service.py**
   - Contains `report_error` signal
   - Connects FBC and RPC service error signals to its own signal
   - Impact: May need to update signal connections or handling

4. **src/commander/presenters/node_tree_presenter_logic.py**
   - Contains `_report_error` method
   - Impact: Need to update to use new error reporting system

5. **src/commander/presenters/node_tree_presenter.py**
   - Contains `_report_error` method
   - Calls `_report_error` in multiple error scenarios (FBC/RPC processing, command errors)
   - Impact: Need to update to use new error reporting system

6. **src/commander/ui/commander_window.py**
   - Connects to `commander_service.report_error` signal
   - Impact: May need to update signal handling

7. **src/commander/services/fbc_command_service.py**
   - Contains `report_error` signal
   - Emits error signals during command queuing
   - Impact: May need to update signal connections

8. **src/commander/services/rpc_command_service.py**
   - Contains `report_error` signal
   - Emits error signals during command queuing
   - Impact: May need to update signal connections

### Error Reporting Providers
1. **src/commander/services/error_handler.py** (Original)
   - Provides `report_error` method
   - Provides specialized error handling methods

2. **src/commander/services/logging_service.py**
   - Provides `report_error` method
   - Impact: Method will be deprecated in favor of new system

## Refactored State

### Error Reporting System
1. **src/commander/services/error_reporting/interface.py**
   - Defines `ErrorReporter` abstract base class
   - Defines `StructuredError` data class

2. **src/commander/services/error_reporting/reporter.py**
   - Implements `ErrorReporterImpl` concrete class
   - Provides Qt signal for UI updates

3. **src/commander/services/error_reporting/delegation_pattern.md**
   - Defines delegation pattern for error handling

## Impact Summary

### High Impact Changes
- Replace direct `ErrorHandler` instantiation with `ErrorReporterImpl`
- Update all `_report_error` methods to use structured error reporting
- Update signal connections to use new error reporting system

### Medium Impact Changes
- Update modules that connect to error signals (FBC/RPC services, Commander service)
- Update UI components that handle error signals

### Low Impact Changes
- Deprecate old `report_error` methods in services
- Update error handling in presenters

## Required Test Coverage

### Unit Tests
1. **ErrorReporterImpl Tests**
   - Test `report_error` method with various `StructuredError` configurations
   - Test `report_simple_error` method with various parameters
   - Test Qt signal emission
   - Test logging output for different severity levels
   - Test exception traceback logging

2. **Integration Tests**
   - Test error reporting from each consumer module
   - Test signal connections and propagation
   - Test UI updates through Qt signals
   - Test logging output to files

### Test Scenarios
1. **Basic Error Reporting**
   - Simple error message reporting
   - Error with exception object
   - Error with different severity levels

2. **Structured Error Reporting**
   - Full `StructuredError` object reporting
   - Error with context information
   - Error with custom timestamp

3. **UI Integration**
   - Qt signal emission with correct parameters
   - Status message duration handling
   - Error message formatting

4. **Logging Integration**
   - Error logging to console
   - Error logging to files
   - Exception traceback logging
   - Different log levels (ERROR, WARNING, INFO)

5. **Consumer Module Integration**
   - CommanderPresenter error reporting
   - NodeTreePresenter error reporting
   - FBC/RPC service error signal handling
   - CommanderService error signal propagation
   - MainWindow error handler integration

### Test Coverage Goals
- **Branch Coverage**: Minimum 90% for all error reporting code paths
- **Function Coverage**: 100% for all error reporting methods
- **Integration Coverage**: Test all consumer-provider interactions
- **UI Coverage**: Test Qt signal emission and handling
- **Logging Coverage**: Test all logging scenarios and outputs

## Migration Strategy

### Phase 1: Implementation
1. Complete implementation of `ErrorReporterImpl`
2. Update all consumer modules to use new error reporting system
3. Maintain backward compatibility during transition

### Phase 2: Testing
1. Run unit tests for new error reporting system
2. Run integration tests for all consumer modules
3. Verify UI integration and signal handling
4. Verify logging integration and output

### Phase 3: Cleanup
1. Remove deprecated error reporting methods
2. Remove old `ErrorHandler` class
3. Update documentation and comments