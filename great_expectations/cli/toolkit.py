import datetime
import os
import subprocess
import sys
from typing import Union

import click

from great_expectations import DataContext
from great_expectations import exceptions as ge_exceptions
from great_expectations.cli.datasource import (
    get_batch_kwargs,
    select_datasource,
)
from great_expectations.cli.docs import build_docs
from great_expectations.cli.util import cli_message
from great_expectations.core import ExpectationSuite
from great_expectations.core.id_dict import BatchKwargs
from great_expectations.data_asset import DataAsset
from great_expectations.data_context.types.resource_identifiers import (
    ValidationResultIdentifier,
)
from great_expectations.profile import BasicSuiteBuilderProfiler


def create_expectation_suite(
    context,
    datasource_name=None,
    batch_kwargs_generator_name=None,
    generator_asset=None,
    batch_kwargs=None,
    expectation_suite_name=None,
    additional_batch_kwargs=None,
    empty_suite=False,
    show_intro_message=False,
    open_docs=False,
    profiler_configuration="demo",
):
    """
    Create a new expectation suite.

    :return: a tuple: (success, suite name)
    """
    if show_intro_message and not empty_suite:
        cli_message(
            "\n<cyan>========== Create sample Expectations ==========</cyan>\n\n"
        )

    data_source = select_datasource(context, datasource_name=datasource_name)
    if data_source is None:
        # select_datasource takes care of displaying an error message, so all is left here is to exit.
        sys.exit(1)

    datasource_name = data_source.name

    if expectation_suite_name in context.list_expectation_suite_names():
        tell_user_suite_exists(expectation_suite_name)
        sys.exit(1)

    if (
        batch_kwargs_generator_name is None
        or generator_asset is None
        or batch_kwargs is None
    ):
        (
            datasource_name,
            batch_kwargs_generator_name,
            generator_asset,
            batch_kwargs,
        ) = get_batch_kwargs(
            context,
            datasource_name=datasource_name,
            batch_kwargs_generator_name=batch_kwargs_generator_name,
            generator_asset=generator_asset,
            additional_batch_kwargs=additional_batch_kwargs,
        )
        # In this case, we have "consumed" the additional_batch_kwargs
        additional_batch_kwargs = {}

    if expectation_suite_name is None:
        default_expectation_suite_name = _get_default_expectation_suite_name(
            batch_kwargs, generator_asset
        )
        while True:
            expectation_suite_name = click.prompt(
                "\nName the new expectation suite",
                default=default_expectation_suite_name,
                show_default=True,
            )
            if expectation_suite_name in context.list_expectation_suite_names():
                tell_user_suite_exists(expectation_suite_name)
            else:
                break

    if empty_suite:
        create_empty_suite(context, expectation_suite_name, batch_kwargs)
        return True, expectation_suite_name

    profiling_results = _profile_to_create_a_suite(
        additional_batch_kwargs,
        batch_kwargs,
        batch_kwargs_generator_name,
        context,
        datasource_name,
        expectation_suite_name,
        generator_asset,
        profiler_configuration,
    )

    build_docs(context, view=False)
    if open_docs:
        _attempt_to_open_validation_results_in_data_docs(context, profiling_results)

    return True, expectation_suite_name


def _profile_to_create_a_suite(
    additional_batch_kwargs,
    batch_kwargs,
    batch_kwargs_generator_name,
    context,
    datasource_name,
    expectation_suite_name,
    generator_asset,
    profiler_configuration,
):
    click.prompt(
        """
Great Expectations will choose a couple of columns and generate expectations about them
to demonstrate some examples of assertions you can make about your data. 
    
Press Enter to continue
""",
        default=True,
        show_default=False,
    )
    # TODO this may not apply
    cli_message("\nGenerating example Expectation Suite...")
    run_id = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S.%fZ")
    profiling_results = context.profile_data_asset(
        datasource_name,
        batch_kwargs_generator_name=batch_kwargs_generator_name,
        data_asset_name=generator_asset,
        batch_kwargs=batch_kwargs,
        profiler=BasicSuiteBuilderProfiler,
        profiler_configuration=profiler_configuration,
        expectation_suite_name=expectation_suite_name,
        run_id=run_id,
        additional_batch_kwargs=additional_batch_kwargs,
    )
    if not profiling_results["success"]:
        _raise_profiling_errors(profiling_results)
    return profiling_results


def _raise_profiling_errors(profiling_results):
    if (
        profiling_results["error"]["code"]
        == DataContext.PROFILING_ERROR_CODE_SPECIFIED_DATA_ASSETS_NOT_FOUND
    ):
        raise ge_exceptions.DataContextError(
            """Some of the data assets you specified were not found: {0:s}    
            """.format(
                ",".join(profiling_results["error"]["not_found_data_assets"])
            )
        )
    raise ge_exceptions.DataContextError(
        "Unknown profiling error code: " + profiling_results["error"]["code"]
    )


def _attempt_to_open_validation_results_in_data_docs(context, profiling_results):
    try:
        # TODO this is really brittle and not covered in tests
        validation_result = profiling_results["results"][0][1]
        validation_result_identifier = ValidationResultIdentifier.from_object(
            validation_result
        )
        context.open_data_docs(resource_identifier=validation_result_identifier)
    except (KeyError, IndexError):
        context.open_data_docs()


def _get_default_expectation_suite_name(batch_kwargs, generator_asset):
    if generator_asset:
        suite_name = f"{generator_asset}.warning"
    elif "query" in batch_kwargs:
        suite_name = "query.warning"
    elif "path" in batch_kwargs:
        try:
            # Try guessing a filename
            filename = os.path.split(os.path.normpath(batch_kwargs["path"]))[1]
            # Take all but the last part after the period
            filename = ".".join(filename.split(".")[:-1])
            suite_name = str(filename) + ".warning"
        except (OSError, IndexError):
            suite_name = "warning"
    else:
        suite_name = "warning"
    return suite_name


def tell_user_suite_exists(suite_name: str) -> None:
    cli_message(
        f"""<red>An expectation suite named `{suite_name}` already exists.</red>
  - If you intend to edit the suite please use `great_expectations suite edit {suite_name}`."""
    )


def create_empty_suite(context: DataContext, expectation_suite_name: str, batch_kwargs) -> None:
    suite = context.create_expectation_suite(
        expectation_suite_name, overwrite_existing=False
    )
    suite.add_citation(comment="New suite added via CLI", batch_kwargs=batch_kwargs)
    context.save_expectation_suite(suite, expectation_suite_name)


def launch_jupyter_notebook(notebook_path: str) -> None:
    subprocess.call(["jupyter", "notebook", notebook_path])


def load_batch(context: DataContext, suite: Union[str, ExpectationSuite], batch_kwargs: Union[dict, BatchKwargs]) -> DataAsset:
    batch: DataAsset = context.get_batch(batch_kwargs, suite)
    assert isinstance(
        batch, DataAsset
    ), "Batch failed to load. Please check your batch_kwargs"
    return batch
