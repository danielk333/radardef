import logging
from pathlib import Path
from typing import Optional

from tqdm import tqdm

from radardef import RadarStation
from radardef.collections import (
    ConverterCollection,
    DataLoaderCollection,
    FormatCollection,
)
from radardef.components import DataLoader
from radardef.radar_stations import ESR, TSDR, Eiscat3D, EiscatUHF, EiscatVHF, Mu, Pansy
from radardef.tools.global_mpi import get_mpi
from radardef.types import (
    DishDiameter,
    Eiscat3DLocation,
    EiscatUHFLocation,
    ExpDef,
    SourceFormat,
    TargetFormat,
)


class RadarDef:
    """
    A tool to expose the radar station data processing components from several radar stations in one place.
    Loading and converting data from multiple formats at once, radar specifications from all radar stations
    available in one place.
    """

    __logger = logging.getLogger(__name__)

    @property
    def radar_stations(self) -> list[str]:
        """All available radarstations"""
        return list(self.__radars.keys())

    @property
    def converter_collection(self) -> ConverterCollection:
        """Collection of all converters"""
        return self.__converter_collection

    @property
    def data_loader_collection(self) -> DataLoaderCollection:
        """Collection of all data loader"""
        return self.__data_loader_collection

    @property
    def format_collection(self) -> FormatCollection:
        """Collection for format validation"""
        return self.__format_collection

    def __init__(self) -> None:
        self.__converter_collection = ConverterCollection([])
        self.__data_loader_collection = DataLoaderCollection([])
        self.__format_collection = FormatCollection([])

        self.__radars: dict[str, RadarStation] = dict()

        for location_3d in Eiscat3DLocation:
            self.add_radar(Eiscat3D(location_3d))
        for location_uhf in EiscatUHFLocation:
            self.add_radar(EiscatUHF(location_uhf))
        for dish_diameter in DishDiameter:
            self.add_radar(ESR(dish_diameter))

        self.add_radars([Mu(), Pansy(), TSDR(), EiscatVHF()])

    def add_radar(self, radar_station: RadarStation) -> None:
        """Add one radar station to the collection, then reload the collections"""
        self.__radars[radar_station.station_id.lower()] = radar_station
        self.__converter_collection.add_converters(radar_station.converters.get_converters())
        self.__data_loader_collection.add_data_loaders(radar_station.data_loaders.get_data_loaders())
        if radar_station.validator:
            self.__format_collection.add_validator(radar_station.validator)

    def add_radars(self, radar_stations: list[RadarStation]) -> None:
        """Add several radar stations to the collection, then reload the collections"""
        for radar in radar_stations:
            self.__radars[radar.station_id.lower()] = radar
            self.__converter_collection.add_converters(radar.converters.get_converters())
            self.__data_loader_collection.add_data_loaders(radar.data_loaders.get_data_loaders())
            if radar.validator:
                self.__format_collection.add_validator(radar.validator)

    def delete_radar(self, key: str) -> None:
        """Remove a radar station, key needs to match station id"""

        try:
            del self.__radars[key]
        except KeyError:
            self.__logger.info("No radar deleted, key does not exist")

    def get_radar(self, id: str) -> RadarStation | None:
        """Get a specific radar station, key needs to match station id"""
        try:
            return self.__radars[id.lower()]
        except KeyError:
            self.__logger.info(f"No radar available with id: {id}")
            return None

    def get_source_format(self, path: Path) -> SourceFormat:
        """Source format of the given path"""
        return self.__format_collection.get_format(path)

    def is_source_format(self, path: Path, source_format: SourceFormat) -> bool:
        """Determines if the path is the given source format"""
        return self.__format_collection.is_format(path, self._validate_source_format(source_format))

    def available_target_formats(self, source_format: SourceFormat) -> list[TargetFormat]:
        """
        Get all target formats that is supported by the available converters for a specific source format
        """
        return self.converter_collection.available_target_formats(source_format)

    def convert(
        self,
        raw_paths: list[str] | list[Path] | str | Path,
        target_format: TargetFormat,
        output_directory: str,
        progress: bool = False,
    ) -> list[Path] | None:
        """
        Convert data to a target format

        Args:
            raw_paths: One or several paths to files/folders to convert.
                Eiscat matlab files must be a folder and not a specific file
            target_format: Format to convert to
            output_directory: Path to output directory to store the converted data

        Returns:
            Paths to the converted files

        """

        if not isinstance(raw_paths, list):
            raw_paths = [raw_paths]  # type: ignore[assignment]

        roots = self._get_root_directories(raw_paths)  # type: ignore[arg-type]
        path_and_format = self._get_source_formats(roots, self.__format_collection)
        target_format = self._validate_target_format(target_format)

        output = []
        comm = get_mpi()
        if progress and comm.rank == 0:
            pbar = tqdm(
                desc="Conversion ",
                total=len(path_and_format),
                position=comm.size + 1,
            )
        else:
            pbar = None

        for path, format in path_and_format:
            ret = self.converter_collection.convert(
                path,
                format,
                target_format,
                Path(output_directory).resolve(),
                progress=progress,
            )

            if pbar and comm.rank == 0:
                pbar.update(1)

            if ret:
                output += ret

        return output

    def load_data(
        self,
        path: Path | str,
        converted_format: TargetFormat = TargetFormat.UNKNOWN,
        experiment: Optional[ExpDef] = None,
    ) -> DataLoader | None:
        """
        Load data from a converted file

        Args:
            path: Path to file to load data from
            converted_format (optional): Converted format of the data,

        Returns:
            DataLoader
        """

        return self.data_loader_collection.load_data(
            Path(path).resolve(), self._validate_target_format(converted_format), experiment
        )

    def _validate_source_format(self, source_format: SourceFormat) -> SourceFormat:
        """Makes sure that the input is of kind SourceFormat"""
        try:
            source_format = SourceFormat(source_format.lower())
        except ValueError:
            source_format = SourceFormat.UNKNOWN
        return source_format

    def _validate_target_format(self, target_format: TargetFormat) -> TargetFormat:
        """Makes sure that the input is of kind TargetFormat"""
        try:
            target_format = TargetFormat(target_format.lower())
        except ValueError:
            target_format = TargetFormat.UNKNOWN
        return target_format

    def _get_root_directories(self, raw_paths: list[str] | list[Path]) -> list[Path]:
        """
        Returns a list of root directories for any directory given and
        any path to a file

        Args:
            paths: Paths to files and directories

        Returns:
            list containing the files listed in the input path and
            the root directories for each directory path listed
        """

        def root_folders(path: Path) -> list[Path]:
            """Returns the root folders of a directory"""
            root_directories = []
            # if folder is a root folder
            if path.is_dir() and not [i for i in path.iterdir() if i.is_dir()]:
                root_directories.append(path)
            # else find root
            else:
                for f in path.iterdir():
                    if f.is_dir():
                        if not [i for i in f.iterdir() if i.is_dir()]:
                            root_directories.append(f)
                        else:
                            root_directories.extend(root_folders(f))
            return root_directories

        dirs = []
        for raw_path in raw_paths:
            path = Path(raw_path).resolve()
            if path.is_dir():
                dirs.extend(root_folders(path))
            elif path.is_file():
                dirs.append(path)
        return dirs

    def _get_source_formats(
        self, paths: list[Path], format_validator: FormatCollection
    ) -> list[tuple[Path, SourceFormat]]:
        """
        Extract format for a folder (assuming all types in the folder has
        the same format and no subfolders) or individual files

        Args:
            paths: List of paths to directories and files
            format_validator: FormatCollection object that contains format checkers

        """

        source_formats = []
        for path in paths:
            if path.is_dir():
                files = [f for f in path.iterdir() if f.is_file()]
                if files is not None:
                    source_formats.append((path, format_validator.get_format(files[0])))
                else:
                    source_formats.append((path, SourceFormat.UNKNOWN))
            elif path.is_file():
                source_formats.append((path, format_validator.get_format(path)))

        return source_formats
