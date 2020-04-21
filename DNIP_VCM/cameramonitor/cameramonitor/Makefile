VERSION=2.4
PACKAGE_NAME=cameramonitor
BUILD_DATE=$(shell date "+%Y%m%d%H%M")
BUILD_TAG=${PACKAGE_NAME}-${VERSION}-${BUILD_DATE}

TARGET = cameramonitor
CXX = g++
CXXFLAGS = -std=c++11 -ggdb3 -O2 -Wall
OEXT = o

INCLUDES = -I/nfs/BaseGroup/3rdparty/boost_1_67_0/install_dir_linux_x64/include -I/nfs/BaseGroup/3rdparty/cpprestsdk-2.10.1/Release/include  -I/nfs/BaseGroup/3rdparty/openssl_1_0_2g/install_dir_linux_x64_fPIC/include
DEP_LIBS = -L/nfs/BaseGroup/3rdparty/boost_1_67_0/install_dir_linux_x64/lib -L/nfs/BaseGroup/3rdparty/cpprestsdk-2.10.1/Release/build.release.linux_x64/Binaries  -L/nfs/BaseGroup/3rdparty/openssl_1_0_2g/install_dir_linux_x64_fPIC/lib -Wl,-Bstatic  -lcpprest -lboost_system -lboost_filesystem -lboost_program_options -llog4cpp -lssl -lcrypto -Wl,-Bdynamic -lpthread -ldl

all : format $(TARGET) 

## source and object files 
SRCS = AlgoParameter.cpp \
	Algoparainstance.cpp\
	AppmgClient.cpp\
	Camera.cpp\
	Config.cpp\
	ETCDWrapper.cpp\
	main.cpp\
	Utility.cpp\
	VideoCaptureApp.cpp\
	VideoCaptureManager.cpp\
    AESCrypto.cpp

OBJS = $(SRCS:.cpp=.$(OEXT))

# =============
# File suffixes
# =============
.SUFFIXES: .cpp .$(OEXT)

# ====================
#compile all cpp files
# ===================
%.${OEXT}: %.cpp
	${CXX} ${CXXFLAGS} ${INCLUDES} -DBUILD_TAG=${BUILD_TAG} -c $<;

# Executable binary
$(TARGET): $(OBJS) 
	$(CXX) ${CXXFLAGS} -o $@ $^ $(DEP_LIBS)

format:
	dos2unix *.cpp

.PHONY: clean
clean:
	rm -f *.$(OEXT) $(TARGET) 
