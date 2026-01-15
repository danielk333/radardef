import logging
from pathlib import Path

from radardef.collections import (
    ConverterCollection,
    DataLoaderCollection,
    FormatCollection,
)
from radardef.components import DataLoader, RadarStation
from radardef.radar_stations import ESR, TSDR, Eiscat3D, EiscatUHF, EiscatVHF, Mu, Pansy
from radardef.types import SourceFormat, TargetFormat
from radardef.types import Eiscat3DLocation, EiscatUHFLocation, DishDiameter


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
        return self.__data_loader

    @property
    def format_collection(self) -> FormatCollection:
        """Collection for format validation"""
        return self.__format_collection

    def __init__(self) -> None:

        self.__radars: dict[str, RadarStation] = dict()

        for location_3d in Eiscat3DLocation:
            self.add_radar(Eiscat3D(location_3d))
        for location_uhf in EiscatUHFLocation:
            self.add_radar(EiscatUHF(location_uhf))
        for dish_diameter in DishDiameter:
            self.add_radar(ESR(dish_diameter))

        self.add_radars([Mu(), Pansy(), TSDR(), EiscatVHF()])

        self.reload_collections()

    def reload_collections(self) -> None:
        """Reload all collections, if new radar stations has been added"""
        self.__converter_collection = ConverterCollection(list(self.__radars.values()))
        self.__format_collection = FormatCollection(list(self.__radars.values()))
        self.__data_loader = DataLoaderCollection(list(self.__radars.values()))

    def add_radar(self, radar_station: RadarStation) -> None:
        """Add one radar station to the collection, then reload the collections"""
        self.__radars[radar_station.station_id.lower()] = radar_station
        self.reload_collections()

    def add_radars(self, radar_stations: list[RadarStation]) -> None:
        """Add several radar stations to the collection, then reload the collections"""
        for radar in radar_stations:
            self.__radars[radar.station_id.lower()] = radar
        self.reload_collections()

    def delete_radar(self, key: str) -> None:
        """Remove a radar station, key needs to match station id"""

        try:
            del self.__radars[key]
        except KeyError:
            self.__logger.info("No radar deleted, key does not exist")
        self.reload_collections()

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

    def convert(
        self,
        raw_paths: list[str] | list[Path] | str | Path,
        target_format: TargetFormat,
        output_directory: str,
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
        try:
            paths, source_formats = zip(*path_and_format)
        except ValueError:
            self.__logger.error("Input path/paths is not a valid file/directory")
            return None

        return self.__converter_collection.convert(
            paths,
            source_formats,
            self._validate_target_format(target_format),
            Path(output_directory).resolve(),
        )

    def load_data(
        self,
        path: Path | str,
        converted_format: TargetFormat = TargetFormat.UNKNOWN,
    ) -> DataLoader | None:
        """
        Load data from a converted file

        Args:
            path: Path to file to load data from
            converted_format (optional): Converted format of the data,

        Returns:
            DataLoader
        """

        return self.__data_loader.load_data(
            Path(path).resolve(),
            self._validate_target_format(converted_format),
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
